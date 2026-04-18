from __future__ import annotations

from pathlib import Path

import pytest

from app.db.database import get_connection
from app.db.repositories import (
    PlayerRepository,
    ResultRepository,
    TournamentRepository,
)
from app.services.import_review import build_import_rating_preview
from app.services.import_xlsx import import_tournament_rows
from app.services.tournament_lifecycle import transition_tournament_status


pytestmark = pytest.mark.integration


def _create_player(player_repo: PlayerRepository, *, last_name: str, first_name: str) -> int:
    return player_repo.create(
        {
            "last_name": last_name,
            "first_name": first_name,
            "middle_name": None,
            "birth_date": None,
            "gender": None,
            "coach": None,
            "club": None,
            "notes": None,
        }
    )


def _create_result_fixture(
    *,
    tournaments: TournamentRepository,
    results: ResultRepository,
    name: str,
    category_code: str | None,
    status: str,
    tournament_date: str,
    rows: list[tuple[int, int]],
) -> int:
    tournament_id = tournaments.create(
        {
            "name": name,
            "date": tournament_date,
            "category_code": category_code,
            "league_code": None,
            "source_files": "[]",
            "status": status,
            "has_draft_changes": 0 if status == "published" else 1,
        }
    )
    for place, (player_id, points_total) in enumerate(rows, start=1):
        results.create(
            {
                "tournament_id": tournament_id,
                "player_id": player_id,
                "place": place,
                "score_set": 0,
                "score_sector20": 0,
                "score_big_round": 0,
                "rank_set": None,
                "rank_sector20": None,
                "rank_big_round": None,
                "points_classification": 0,
                "points_place": points_total,
                "points_total": points_total,
                "calc_version": "tests",
            }
        )
    return tournament_id


def test_official_rating_uses_only_published_tournaments_until_publish(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "rating-status-filter.db")
    players = PlayerRepository(connection)
    tournaments = TournamentRepository(connection)
    results = ResultRepository(connection)

    published_player_id = _create_player(players, last_name="Adams", first_name="Alice")
    _create_result_fixture(
        tournaments=tournaments,
        results=results,
        name="Published Cup",
        category_code="U12",
        status="published",
        tournament_date="2026-01-10",
        rows=[(published_player_id, 90)],
    )

    apply_report = import_tournament_rows(
        connection=connection,
        rows=[
            {
                "fio": "Brown Bob",
                "birth": "2011-04-01",
                "place": 1,
                "score_set": 120,
                "score_sector20": 0,
                "score_big_round": 0,
            }
        ],
        tournament_name="Draft Import",
        tournament_date="2026-02-10",
        category_code="U12",
        source_files=["/tmp/import.xlsx"],
    )

    before_publish = results.list_results_for_rating(category_code="U12")
    before_publish_all = results.list_results_for_rating(
        category_code="U12",
        statuses=["published", "draft"],
    )

    assert [row["last_name"] for row in before_publish] == ["Adams"]
    assert {str(row["last_name"]).lower() for row in before_publish_all} == {"adams", "brown"}

    assert transition_tournament_status(
        connection=connection,
        tournament_id=apply_report.tournament_id,
        to_status="review",
        context={"actor": "tests"},
    )["ok"] is True
    assert transition_tournament_status(
        connection=connection,
        tournament_id=apply_report.tournament_id,
        to_status="confirmed",
        context={"actor": "tests"},
    )["ok"] is True
    assert transition_tournament_status(
        connection=connection,
        tournament_id=apply_report.tournament_id,
        to_status="published",
        context={"actor": "tests"},
    )["ok"] is True

    after_publish = results.list_results_for_rating(category_code="U12")
    assert {str(row["last_name"]).lower() for row in after_publish} == {"adams", "brown"}


def test_build_import_rating_preview_uses_published_baseline_plus_current_draft_only(
    tmp_path: Path,
) -> None:
    connection = get_connection(tmp_path / "import-rating-preview.db")
    players = PlayerRepository(connection)
    tournaments = TournamentRepository(connection)
    results = ResultRepository(connection)

    alice_id = _create_player(players, last_name="Adams", first_name="Alice")
    bob_id = _create_player(players, last_name="Brown", first_name="Bob")
    charlie_id = _create_player(players, last_name="Clark", first_name="Charlie")
    zack_id = _create_player(players, last_name="Zed", first_name="Zack")

    _create_result_fixture(
        tournaments=tournaments,
        results=results,
        name="Published Baseline",
        category_code="U14",
        status="published",
        tournament_date="2026-01-05",
        rows=[(alice_id, 100), (bob_id, 90)],
    )
    _create_result_fixture(
        tournaments=tournaments,
        results=results,
        name="Other Draft",
        category_code="U14",
        status="draft",
        tournament_date="2026-01-20",
        rows=[(zack_id, 999)],
    )
    draft_id = _create_result_fixture(
        tournaments=tournaments,
        results=results,
        name="Current Draft",
        category_code="U14",
        status="draft",
        tournament_date="2026-02-01",
        rows=[(charlie_id, 120), (bob_id, 60)],
    )

    preview = build_import_rating_preview(connection=connection, tournament_id=draft_id, n_value=6)

    assert preview.available is True
    assert preview.reason is None
    assert [(row.fio, row.place, row.points) for row in preview.before_rows] == [
        ("Adams Alice", 1, 100),
        ("Brown Bob", 2, 90),
    ]
    assert [(row.fio, row.place, row.points) for row in preview.after_rows] == [
        ("Brown Bob", 1, 150),
        ("Clark Charlie", 2, 120),
        ("Adams Alice", 3, 100),
    ]
    assert [
        (
            row.fio,
            row.old_place,
            row.new_place,
            row.place_delta,
            row.old_points,
            row.new_points,
            row.points_delta,
        )
        for row in preview.rows
    ] == [
        ("Brown Bob", 2, 1, 1, 90, 150, 60),
        ("Clark Charlie", None, 2, None, 0, 120, 120),
        ("Adams Alice", 1, 3, -2, 100, 100, 0),
    ]


def test_build_import_rating_preview_returns_reason_when_category_missing(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "import-rating-preview-missing-category.db")
    tournaments = TournamentRepository(connection)

    tournament_id = tournaments.create(
        {
            "name": "Draft Without Category",
            "date": "2026-02-10",
            "category_code": None,
            "league_code": None,
            "source_files": "[]",
            "status": "draft",
            "has_draft_changes": 1,
        }
    )

    preview = build_import_rating_preview(connection=connection, tournament_id=tournament_id, n_value=6)

    assert preview.available is False
    assert preview.rows == []
    assert preview.reason is not None
    assert "category" in preview.reason.lower()

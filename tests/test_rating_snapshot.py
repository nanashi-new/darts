from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.db.database import get_connection
from app.db.repositories import PlayerRepository, ResultRepository, TournamentRepository
from app.services.audit_log import RATING_SNAPSHOT_CREATED
from app.services.import_xlsx import import_tournament_rows
from app.services.tournament_correction import correct_tournament
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


def _create_tournament_with_results(
    *,
    connection,
    category_code: str | None,
    status: str,
    tournament_date: str,
    rows: list[tuple[str, str, int]],
) -> int:
    tournaments = TournamentRepository(connection)
    players = PlayerRepository(connection)
    results = ResultRepository(connection)
    tournament_id = tournaments.create(
        {
            "name": f"Tournament {tournament_date}",
            "date": tournament_date,
            "category_code": category_code,
            "league_code": None,
            "source_files": "[]",
            "status": status,
            "has_draft_changes": 0 if status == "published" else 1,
        }
    )
    for place, (last_name, first_name, points_total) in enumerate(rows, start=1):
        player_id = _create_player(players, last_name=last_name, first_name=first_name)
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


def test_create_rating_snapshot_skips_when_tournament_has_no_category(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "rating-snapshot-skip.db")
    tournament_id = _create_tournament_with_results(
        connection=connection,
        category_code=None,
        status="published",
        tournament_date="2026-04-01",
        rows=[("Ivanov", "Ivan", 80)],
    )

    from app.services.rating_snapshot import create_rating_snapshot_for_tournament_publish

    result = create_rating_snapshot_for_tournament_publish(
        connection=connection,
        tournament_id=tournament_id,
        n_value=6,
        operation_group_id="op-no-category",
    )

    assert result.created is False
    assert result.reason is not None
    assert "category" in result.reason.lower()


def test_publish_creates_category_snapshot_and_audit_event(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "rating-snapshot-publish.db")
    tournament_id = _create_tournament_with_results(
        connection=connection,
        category_code="U14",
        status="draft",
        tournament_date="2026-04-05",
        rows=[("Adams", "Alice", 100), ("Brown", "Bob", 90)],
    )
    operation_group_id = "op-snapshot-publish"

    assert transition_tournament_status(
        connection=connection,
        tournament_id=tournament_id,
        to_status="review",
        context={"actor": "tests", "operation_group_id": operation_group_id},
    )["ok"] is True
    assert transition_tournament_status(
        connection=connection,
        tournament_id=tournament_id,
        to_status="confirmed",
        context={"actor": "tests", "operation_group_id": operation_group_id},
    )["ok"] is True
    assert transition_tournament_status(
        connection=connection,
        tournament_id=tournament_id,
        to_status="published",
        context={"actor": "tests", "operation_group_id": operation_group_id},
    )["ok"] is True

    from app.services.rating_snapshot import list_rating_snapshot_rows, list_rating_snapshot_sessions

    sessions = list_rating_snapshot_sessions(connection, scope_type="category", scope_key="U14")
    assert len(sessions) == 1
    rows = list_rating_snapshot_rows(
        connection,
        snapshot_created_at=sessions[0].created_at,
        scope_type="category",
        scope_key="U14",
    )
    assert [(row.position, row.fio, row.points) for row in rows] == [
        (1, "Adams Alice", 100),
        (2, "Brown Bob", 90),
    ]
    assert rows[0].rolling_basis[0].tournament_id == tournament_id
    assert rows[0].rolling_basis[0].points_total == 100

    audit_rows = connection.execute(
        """
        SELECT operation_group_id, context_json
        FROM audit_log
        WHERE event_type = ?
        ORDER BY id ASC
        """,
        (RATING_SNAPSHOT_CREATED,),
    ).fetchall()
    assert len(audit_rows) == 1
    assert audit_rows[0]["operation_group_id"] == operation_group_id
    payload = json.loads(str(audit_rows[0]["context_json"]))
    assert payload["scope_type"] == "category"
    assert payload["scope_key"] == "U14"


def test_import_publish_reuses_operation_group_id_for_snapshot_event(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "rating-snapshot-import-publish.db")
    apply_report = import_tournament_rows(
        connection=connection,
        rows=[
            {
                "fio": "Clark Cara",
                "birth": "2012-03-04",
                "place": 1,
                "score_set": 75,
                "score_sector20": 0,
                "score_big_round": 0,
            }
        ],
        tournament_name="Import Publish Cup",
        tournament_date="2026-04-06",
        category_code="U12",
        operation_group_id="op-import-publish-snapshot",
    )

    for target_status in ("review", "confirmed", "published"):
        assert transition_tournament_status(
            connection=connection,
            tournament_id=apply_report.tournament_id,
            to_status=target_status,
            context={"actor": "tests", "operation_group_id": apply_report.operation_group_id},
        )["ok"] is True

    audit_row = connection.execute(
        """
        SELECT operation_group_id
        FROM audit_log
        WHERE event_type = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (RATING_SNAPSHOT_CREATED,),
    ).fetchone()
    assert audit_row is not None
    assert audit_row["operation_group_id"] == apply_report.operation_group_id


def test_correction_does_not_create_snapshot_until_republish(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "rating-snapshot-correction.db")
    tournament_id = _create_tournament_with_results(
        connection=connection,
        category_code="U16",
        status="draft",
        tournament_date="2026-04-07",
        rows=[("Delta", "Dana", 95)],
    )

    assert transition_tournament_status(
        connection=connection,
        tournament_id=tournament_id,
        to_status="review",
        context={"actor": "tests", "operation_group_id": "op-correction"},
    )["ok"] is True
    assert transition_tournament_status(
        connection=connection,
        tournament_id=tournament_id,
        to_status="confirmed",
        context={"actor": "tests", "operation_group_id": "op-correction"},
    )["ok"] is True
    assert transition_tournament_status(
        connection=connection,
        tournament_id=tournament_id,
        to_status="published",
        context={"actor": "tests", "operation_group_id": "op-correction"},
    )["ok"] is True

    from app.services.rating_snapshot import list_rating_snapshot_sessions

    first_sessions = list_rating_snapshot_sessions(connection, scope_type="category", scope_key="U16")
    assert len(first_sessions) == 1

    correction_result = correct_tournament(
        connection=connection,
        tournament_id=tournament_id,
        reason="Fix metadata",
        updates={"name": "Corrected Tournament"},
        actor="tests",
        operation_group_id="op-correction",
    )
    assert correction_result["to_status"] == "review"
    sessions_after_correction = list_rating_snapshot_sessions(connection, scope_type="category", scope_key="U16")
    assert len(sessions_after_correction) == 1

    assert transition_tournament_status(
        connection=connection,
        tournament_id=tournament_id,
        to_status="confirmed",
        context={"actor": "tests", "operation_group_id": "op-correction"},
    )["ok"] is True
    assert transition_tournament_status(
        connection=connection,
        tournament_id=tournament_id,
        to_status="published",
        context={"actor": "tests", "operation_group_id": "op-correction"},
    )["ok"] is True

    final_sessions = list_rating_snapshot_sessions(connection, scope_type="category", scope_key="U16")
    assert len(final_sessions) == 2

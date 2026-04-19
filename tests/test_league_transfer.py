from __future__ import annotations

from pathlib import Path

import pytest

from app.db.database import get_connection
from app.db.repositories import PlayerRepository, ResultRepository, TournamentRepository
from app.services.audit_log import LEAGUE_TRANSFER_CREATED
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


def _create_tournament_with_players(
    *,
    connection,
    league_code: str | None,
    status: str,
    tournament_date: str,
    rows: list[tuple[str, str, int]],
) -> tuple[int, list[int]]:
    tournaments = TournamentRepository(connection)
    players = PlayerRepository(connection)
    results = ResultRepository(connection)
    tournament_id = tournaments.create(
        {
            "name": f"League Tournament {tournament_date}",
            "date": tournament_date,
            "category_code": "U18",
            "league_code": league_code,
            "is_adult_mode": 0,
            "source_files": "[]",
            "status": status,
            "has_draft_changes": 0 if status == "published" else 1,
        }
    )
    player_ids: list[int] = []
    for place, (last_name, first_name, points_total) in enumerate(rows, start=1):
        player_id = _create_player(players, last_name=last_name, first_name=first_name)
        player_ids.append(player_id)
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
    return tournament_id, player_ids


def test_publish_league_tournament_creates_initial_transfer_events_and_audit(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "league-transfer-initial.db")
    tournament_id, player_ids = _create_tournament_with_players(
        connection=connection,
        league_code="PREMIER",
        status="draft",
        tournament_date="2026-04-20",
        rows=[("League", "Alpha", 100), ("League", "Beta", 90)],
    )

    for target in ("review", "confirmed", "published"):
        assert transition_tournament_status(
            connection=connection,
            tournament_id=tournament_id,
            to_status=target,
            context={"actor": "tests", "operation_group_id": "op-league-initial"},
        )["ok"] is True

    from app.services.league_transfer import list_player_league_transfers

    for player_id in player_ids:
        events = list_player_league_transfers(connection, player_id)
        assert len(events) == 1
        assert events[0].from_league_code is None
        assert events[0].to_league_code == "PREMIER"
        assert events[0].source_tournament_id == tournament_id

    audit_rows = connection.execute(
        "SELECT COUNT(*) AS count FROM audit_log WHERE event_type = ?",
        (LEAGUE_TRANSFER_CREATED,),
    ).fetchone()
    assert audit_rows is not None
    assert int(audit_rows["count"]) == 2


def test_same_league_republish_does_not_create_duplicate_transfer(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "league-transfer-same-league.db")
    tournament_id, player_ids = _create_tournament_with_players(
        connection=connection,
        league_code="PREMIER",
        status="draft",
        tournament_date="2026-04-21",
        rows=[("League", "Alpha", 100)],
    )

    for target in ("review", "confirmed", "published"):
        assert transition_tournament_status(
            connection=connection,
            tournament_id=tournament_id,
            to_status=target,
            context={"actor": "tests", "operation_group_id": "op-same-league"},
        )["ok"] is True

    correction = correct_tournament(
        connection=connection,
        tournament_id=tournament_id,
        reason="Metadata only",
        updates={"name": "Renamed"},
        actor="tests",
        operation_group_id="op-same-league",
    )
    assert correction["to_status"] == "review"
    assert transition_tournament_status(
        connection=connection,
        tournament_id=tournament_id,
        to_status="confirmed",
        context={"actor": "tests", "operation_group_id": "op-same-league"},
    )["ok"] is True
    assert transition_tournament_status(
        connection=connection,
        tournament_id=tournament_id,
        to_status="published",
        context={"actor": "tests", "operation_group_id": "op-same-league"},
    )["ok"] is True

    from app.services.league_transfer import list_player_league_transfers

    events = list_player_league_transfers(connection, player_ids[0])
    assert len(events) == 1


def test_changed_league_republish_creates_new_transfer_event(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "league-transfer-changed-league.db")
    tournament_id, player_ids = _create_tournament_with_players(
        connection=connection,
        league_code="FIRST",
        status="draft",
        tournament_date="2026-04-22",
        rows=[("League", "Alpha", 100)],
    )

    for target in ("review", "confirmed", "published"):
        assert transition_tournament_status(
            connection=connection,
            tournament_id=tournament_id,
            to_status=target,
            context={"actor": "tests", "operation_group_id": "op-change-league"},
        )["ok"] is True

    correction = correct_tournament(
        connection=connection,
        tournament_id=tournament_id,
        reason="League moved",
        updates={"league_code": "PREMIER"},
        actor="tests",
        operation_group_id="op-change-league",
    )
    assert correction["to_status"] == "review"
    assert transition_tournament_status(
        connection=connection,
        tournament_id=tournament_id,
        to_status="confirmed",
        context={"actor": "tests", "operation_group_id": "op-change-league"},
    )["ok"] is True
    assert transition_tournament_status(
        connection=connection,
        tournament_id=tournament_id,
        to_status="published",
        context={"actor": "tests", "operation_group_id": "op-change-league"},
    )["ok"] is True

    from app.services.league_transfer import list_player_league_transfers

    events = list_player_league_transfers(connection, player_ids[0])
    assert len(events) == 2
    assert events[0].from_league_code == "FIRST"
    assert events[0].to_league_code == "PREMIER"


def test_build_league_transfer_preview_returns_only_changed_players(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "league-transfer-preview.db")
    baseline_tournament, player_ids = _create_tournament_with_players(
        connection=connection,
        league_code="FIRST",
        status="draft",
        tournament_date="2026-04-23",
        rows=[("League", "Alpha", 100), ("League", "Beta", 90)],
    )
    for target in ("review", "confirmed", "published"):
        assert transition_tournament_status(
            connection=connection,
            tournament_id=baseline_tournament,
            to_status=target,
            context={"actor": "tests", "operation_group_id": "op-preview-baseline"},
        )["ok"] is True

    tournaments = TournamentRepository(connection)
    results = ResultRepository(connection)
    second_tournament = tournaments.create(
        {
            "name": "League Tournament Preview",
            "date": "2026-04-24",
            "category_code": "U18",
            "league_code": "PREMIER",
            "is_adult_mode": 0,
            "source_files": "[]",
            "status": "draft",
            "has_draft_changes": 1,
        }
    )
    results.create(
        {
            "tournament_id": second_tournament,
            "player_id": player_ids[0],
            "place": 1,
            "score_set": 0,
            "score_sector20": 0,
            "score_big_round": 0,
            "rank_set": None,
            "rank_sector20": None,
            "rank_big_round": None,
            "points_classification": 0,
            "points_place": 120,
            "points_total": 120,
            "calc_version": "tests",
        }
    )

    from app.services.league_transfer import build_league_transfer_preview

    preview = build_league_transfer_preview(connection=connection, tournament_id=second_tournament)

    assert preview.available is True
    assert len(preview.rows) == 1
    assert preview.rows[0].player_id == player_ids[0]
    assert preview.rows[0].from_league_code == "FIRST"
    assert preview.rows[0].to_league_code == "PREMIER"

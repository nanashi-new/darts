from __future__ import annotations

import pytest

from app.db.database import get_connection
from app.db.repositories import PlayerRepository, ResultRepository, TournamentRepository
from app.services.audit_log import TOURNAMENT_CREATED
from app.services.recalculate_tournament import recalculate_tournament_results
from app.services.rating_snapshot import list_rating_snapshot_sessions
from app.services.tournament_lifecycle import transition_tournament_status


pytestmark = pytest.mark.integration


def test_create_manual_adult_tournament_creates_draft_results_and_audit(tmp_path) -> None:
    from app.services.manual_tournament import create_manual_adult_tournament

    connection = get_connection(tmp_path / "manual-adult.db")

    report = create_manual_adult_tournament(
        connection=connection,
        tournament_name="Adult Manual Cup",
        tournament_date="2026-04-20",
        league_code="PREMIER",
        rows=[
            {
                "fio": "Adultov Alex",
                "birth": "1989-01-01",
                "place": 1,
                "points_total": 120,
            },
            {
                "fio": "Senior Sara",
                "birth": "1990-02-02",
                "place": 2,
                "points_total": 105,
            },
        ],
        operation_group_id="op-manual-adult",
    )

    tournament = TournamentRepository(connection).get(report.tournament_id)
    assert tournament is not None
    assert tournament["status"] == "draft"
    assert tournament["is_adult_mode"] == 1
    assert tournament["category_code"] is None
    assert tournament["league_code"] == "PREMIER"

    results = ResultRepository(connection).list_with_players(report.tournament_id)
    assert [(row["place"], row["points_total"]) for row in results] == [(1, 120), (2, 105)]
    assert all(int(row["points_classification"] or 0) == 0 for row in results)

    audit_event = connection.execute(
        """
        SELECT event_type, operation_group_id
        FROM audit_log
        WHERE entity_type = 'tournament' AND entity_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (str(report.tournament_id),),
    ).fetchone()
    assert audit_event is not None
    assert audit_event["event_type"] == TOURNAMENT_CREATED
    assert audit_event["operation_group_id"] == "op-manual-adult"


def test_create_manual_adult_tournament_reuses_existing_player_by_identity(tmp_path) -> None:
    from app.services.manual_tournament import create_manual_adult_tournament

    connection = get_connection(tmp_path / "manual-adult-existing-player.db")
    players = PlayerRepository(connection)
    existing_player_id = players.create(
        {
            "last_name": "Adultov",
            "first_name": "Alex",
            "middle_name": None,
            "birth_date": "1989-01-01",
            "gender": None,
            "coach": None,
            "club": None,
            "notes": None,
        }
    )

    report = create_manual_adult_tournament(
        connection=connection,
        tournament_name="Adult Existing Player Cup",
        tournament_date="2026-04-21",
        league_code=None,
        rows=[
            {
                "fio": "Adultov Alex",
                "birth": "1989-01-01",
                "place": 1,
                "points_total": 130,
            }
        ],
    )

    results = ResultRepository(connection).list_with_players(report.tournament_id)
    assert len(results) == 1
    assert int(results[0]["player_id"]) == existing_player_id
    assert len(players.list()) == 1


def test_manual_adult_tournament_publish_creates_adult_snapshots_and_keeps_manual_points(tmp_path) -> None:
    from app.services.league_transfer import list_player_league_transfers
    from app.services.manual_tournament import create_manual_adult_tournament

    connection = get_connection(tmp_path / "manual-adult-publish.db")

    report = create_manual_adult_tournament(
        connection=connection,
        tournament_name="Adult Publish Cup",
        tournament_date="2026-04-23",
        league_code="PREMIER",
        rows=[
            {
                "fio": "Adultov Alex",
                "birth": "1989-01-01",
                "gender": "M",
                "place": 1,
                "points_total": 140,
            },
            {
                "fio": "Senior Sara",
                "birth": "1990-02-02",
                "gender": "W",
                "place": 2,
                "points_total": 125,
            },
        ],
        operation_group_id="op-manual-adult-publish",
    )

    recalc = recalculate_tournament_results(
        connection=connection,
        tournament_id=report.tournament_id,
    )
    assert recalc.results_updated == 2

    for target in ("review", "confirmed", "published"):
        assert transition_tournament_status(
            connection=connection,
            tournament_id=report.tournament_id,
            to_status=target,
            context={"actor": "tests", "operation_group_id": "op-manual-adult-publish"},
        )["ok"] is True

    results = ResultRepository(connection).list_with_players(report.tournament_id)
    assert [(row["place"], row["points_total"], row["calc_version"]) for row in results] == [
        (1, 140, "manual_adult_v1"),
        (2, 125, "manual_adult_v1"),
    ]

    assert len(list_rating_snapshot_sessions(connection, scope_type="adult", scope_key="overall")) == 1
    assert len(list_rating_snapshot_sessions(connection, scope_type="adult", scope_key="men")) == 1
    assert len(list_rating_snapshot_sessions(connection, scope_type="adult", scope_key="women")) == 1

    player_ids = [int(row["player_id"]) for row in results]
    for player_id in player_ids:
        transfers = list_player_league_transfers(connection, player_id)
        assert len(transfers) == 1
        assert transfers[0].to_league_code == "PREMIER"

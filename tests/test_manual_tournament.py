from __future__ import annotations

import pytest

from app.db.database import get_connection
from app.db.repositories import PlayerRepository, ResultRepository, TournamentRepository
from app.services.audit_log import TOURNAMENT_CREATED


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

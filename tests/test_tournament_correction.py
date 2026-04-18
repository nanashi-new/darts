from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.db.database import get_connection
from app.db.repositories import PlayerRepository, ResultRepository, TournamentRepository
from app.services.audit_log import AuditLogService, TOURNAMENT_CORRECTED
from app.services.tournament_correction import TournamentCorrectionError, correct_tournament
from app.services.tournament_lifecycle import transition_tournament_status


pytestmark = pytest.mark.integration


def _publish_tournament(connection, tournament_id: int) -> None:
    assert transition_tournament_status(
        connection=connection,
        tournament_id=tournament_id,
        to_status="review",
        context={"actor": "tests"},
    )["ok"] is True
    assert transition_tournament_status(
        connection=connection,
        tournament_id=tournament_id,
        to_status="confirmed",
        context={"actor": "tests"},
    )["ok"] is True
    assert transition_tournament_status(
        connection=connection,
        tournament_id=tournament_id,
        to_status="published",
        context={"actor": "tests"},
    )["ok"] is True


def test_correction_requires_reason(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "correction_reason.db")
    tournaments = TournamentRepository(connection)
    tournament_id = tournaments.create({"name": "Cup", "date": "2026-02-01", "category_code": "U12"})
    _publish_tournament(connection, tournament_id)

    with pytest.raises(TournamentCorrectionError, match="reason"):
        correct_tournament(
            connection=connection,
            tournament_id=tournament_id,
            reason="",
            actor="tests",
        )


def test_correction_logs_old_new_and_recalculates_results(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "correction_apply.db")
    players = PlayerRepository(connection)
    tournaments = TournamentRepository(connection)
    results = ResultRepository(connection)
    audit = AuditLogService(connection)

    player_id = players.create(
        {
            "last_name": "Ivanov",
            "first_name": "Ivan",
            "middle_name": "I",
            "birth_date": "2012-04-03",
            "gender": "M",
            "coach": None,
            "club": None,
            "notes": None,
        }
    )
    tournament_id = tournaments.create(
        {
            "name": "Spring Cup",
            "date": "2026-03-20",
            "category_code": "U12",
            "league_code": "A",
        }
    )
    results.create(
        {
            "tournament_id": tournament_id,
            "player_id": player_id,
            "place": 1,
            "score_set": 320,
            "score_sector20": 40,
            "score_big_round": 12,
            "rank_set": None,
            "rank_sector20": None,
            "rank_big_round": None,
            "points_classification": 0,
            "points_place": 0,
            "points_total": 0,
            "calc_version": None,
        }
    )

    _publish_tournament(connection, tournament_id)

    result = correct_tournament(
        connection=connection,
        tournament_id=tournament_id,
        reason="Исправлена дата протокола",
        updates={"date": "2026-03-21", "name": "Spring Cup Updated"},
        actor="tests",
        operation_group_id="corr-777",
    )

    assert result["to_status"] == "review"
    assert result["changed_fields"] == ["date", "name"]
    assert result["results_recalculated"] == 1
    assert result["operation_group_id"] == "corr-777"

    tournament = tournaments.get(tournament_id)
    assert tournament is not None
    assert tournament["status"] == "review"
    assert tournament["date"] == "2026-03-21"
    assert tournament["name"] == "Spring Cup Updated"

    result_rows = results.search(tournament_id=tournament_id)
    assert len(result_rows) == 1
    assert result_rows[0]["calc_version"] == "v2"

    correction_events = audit.list_events(event_type=TOURNAMENT_CORRECTED)
    assert len(correction_events) >= 2
    correction_operation_event = next(
        event for event in correction_events if event.title == "Коррекция турнира применена"
    )
    assert correction_operation_event.reason == "Исправлена дата протокола"
    assert correction_operation_event.operation_group_id == "corr-777"
    assert correction_operation_event.entity_id == str(tournament_id)

    old_payload = json.loads(correction_operation_event.old_value_json or "{}")
    new_payload = json.loads(correction_operation_event.new_value_json or "{}")
    assert old_payload["date"] == "2026-03-20"
    assert new_payload["date"] == "2026-03-21"
    assert old_payload["name"] == "Spring Cup"
    assert new_payload["name"] == "Spring Cup Updated"
    assert correction_operation_event.context.get("history_marker") == "correction"

from __future__ import annotations

from pathlib import Path

import pytest

from app.db.database import get_connection
from app.db.repositories import TournamentRepository
from app.services.audit_log import (
    AuditLogService,
    TOURNAMENT_PUBLISHED,
    TOURNAMENT_UPDATED,
)
from app.services.tournament_lifecycle import transition_tournament_status


pytestmark = pytest.mark.integration


def test_transition_logs_old_new_status_and_reason(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "lifecycle.db")
    tournaments = TournamentRepository(connection)
    audit = AuditLogService(connection)

    tournament_id = tournaments.create({"name": "Cup", "date": "2026-01-01", "category_code": "U12"})

    review_result = transition_tournament_status(
        connection=connection,
        tournament_id=tournament_id,
        to_status="review",
        context={"actor": "tests", "reason": "moderation", "operation_group_id": "op-42"},
    )
    assert review_result["ok"] is True

    review_events = audit.list_events(event_type=TOURNAMENT_UPDATED)
    assert review_events
    review_event = review_events[0]
    assert review_event.entity_type == "tournament"
    assert review_event.entity_id == str(tournament_id)
    assert review_event.reason == "moderation"
    assert review_event.old_value_json == '{"status": "draft"}'
    assert review_event.new_value_json == '{"status": "review"}'
    assert review_event.source == "tests"
    assert review_event.operation_group_id == "op-42"

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

    published_events = audit.list_events(event_type=TOURNAMENT_PUBLISHED)
    assert published_events
    assert published_events[0].new_value_json == '{"status": "published"}'

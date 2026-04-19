from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.db.database import get_connection
from app.db.repositories import TournamentRepository
from app.services.import_xlsx import import_tournament_rows
from app.services.tournament_lifecycle import transition_tournament_status


pytestmark = pytest.mark.integration


def _sample_import_rows() -> list[dict[str, object]]:
    return [
        {
            "fio": "Иванов Иван",
            "birth": "2010-01-01",
            "coach": "Coach A",
            "place": 1,
            "score_set": 60,
            "score_sector20": 20,
            "score_big_round": 40,
        }
    ]


def _fetch_audit_status_events(connection, tournament_id: int) -> list[dict[str, object]]:
    rows = connection.execute(
        """
        SELECT event_type, reason, old_value_json, new_value_json, source
        FROM audit_log
        WHERE entity_type = 'tournament'
          AND entity_id = ?
          AND event_type IN ('tournament_updated', 'tournament_published', 'tournament_corrected')
        ORDER BY id ASC
        """,
        (str(tournament_id),),
    ).fetchall()
    return [dict(row) for row in rows]


def test_import_creates_draft_and_happy_path_to_published_with_audit(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "lifecycle-flow.db")
    tournaments = TournamentRepository(connection)

    apply_report = import_tournament_rows(
        connection=connection,
        rows=_sample_import_rows(),
        tournament_name="Imported Cup",
        tournament_date="2026-03-01",
        category_code="U14",
        source_files=["/tmp/imported.xlsx"],
    )

    assert apply_report.tournament_status == "draft"
    created = tournaments.get(apply_report.tournament_id)
    assert created is not None
    assert created["status"] == "draft"
    assert created["has_draft_changes"] == 1
    assert json.loads(str(created["source_files"])) == ["/tmp/imported.xlsx"]

    assert transition_tournament_status(
        connection=connection,
        tournament_id=apply_report.tournament_id,
        to_status="review",
        context={"actor": "tests", "reason": "import moderation"},
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

    published = tournaments.get(apply_report.tournament_id)
    assert published is not None
    assert published["status"] == "published"

    audit_events = _fetch_audit_status_events(connection, apply_report.tournament_id)
    assert len(audit_events) == 3
    assert [event["event_type"] for event in audit_events] == [
        "tournament_updated",
        "tournament_updated",
        "tournament_published",
    ]
    assert [event["old_value_json"] for event in audit_events] == [
        '{"status": "draft"}',
        '{"status": "review"}',
        '{"status": "confirmed"}',
    ]
    assert [event["new_value_json"] for event in audit_events] == [
        '{"status": "review"}',
        '{"status": "confirmed"}',
        '{"status": "published"}',
    ]


def test_negative_transitions_and_correction_requirements(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "lifecycle-negative.db")

    apply_report = import_tournament_rows(
        connection=connection,
        rows=_sample_import_rows(),
        tournament_name="Imported Negative",
        tournament_date="2026-03-02",
        category_code="U16",
    )

    invalid_direct_publish = transition_tournament_status(
        connection=connection,
        tournament_id=apply_report.tournament_id,
        to_status="published",
        context={"actor": "tests"},
    )
    assert invalid_direct_publish["ok"] is False
    assert invalid_direct_publish["error"]["code"] == "invalid_transition"

    review_result = transition_tournament_status(
        connection=connection,
        tournament_id=apply_report.tournament_id,
        to_status="review",
        context={"actor": "tests"},
    )
    assert review_result["ok"] is True

    publish_without_confirm = transition_tournament_status(
        connection=connection,
        tournament_id=apply_report.tournament_id,
        to_status="published",
        context={"actor": "tests"},
    )
    assert publish_without_confirm["ok"] is False
    assert publish_without_confirm["error"]["code"] == "invalid_transition"

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

    without_correction_flow = transition_tournament_status(
        connection=connection,
        tournament_id=apply_report.tournament_id,
        to_status="review",
        context={"actor": "tests"},
    )
    assert without_correction_flow["ok"] is False
    assert without_correction_flow["error"]["code"] == "invalid_transition"

    missing_reason_correction = transition_tournament_status(
        connection=connection,
        tournament_id=apply_report.tournament_id,
        to_status="review",
        context={"actor": "tests", "restore": True, "audit": {"ticket": "OPS-7"}},
    )
    assert missing_reason_correction["ok"] is False
    assert missing_reason_correction["error"]["code"] == "invalid_transition"

    tournament_row = connection.execute(
        "SELECT status FROM tournaments WHERE id = ?",
        (apply_report.tournament_id,),
    ).fetchone()
    assert tournament_row is not None
    assert tournament_row["status"] == "published"

    audit_events = _fetch_audit_status_events(connection, apply_report.tournament_id)
    assert len(audit_events) == 3

from __future__ import annotations

from pathlib import Path

import pytest

from app.db.database import get_connection
from app.db.repositories import TournamentRepository
from app.domain.tournament_lifecycle import TournamentStatus
from app.services.tournament_lifecycle import transition_tournament_status
from app.services.tournament_safe_status import archive_or_cancel_tournament


pytestmark = pytest.mark.integration


def _create_tournament(connection, *, status: str = "draft") -> int:
    return TournamentRepository(connection).create(
        {
            "name": "Safe Status Cup",
            "date": "2026-04-26",
            "category_code": "U12",
            "source_files": "[]",
            "status": status,
            "has_draft_changes": 0 if status == "published" else 1,
        }
    )


def _publish_tournament(connection, tournament_id: int) -> None:
    for target in ("review", "confirmed", "published"):
        assert transition_tournament_status(
            connection=connection,
            tournament_id=tournament_id,
            to_status=target,
            context={"actor": "tests", "operation_group_id": "op-publish"},
        )["ok"] is True


def _restore_point_count(connection) -> int:
    row = connection.execute("SELECT COUNT(*) AS count FROM restore_points").fetchone()
    assert row is not None
    return int(row["count"])


def test_archive_or_cancel_requires_reason(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "safe-status-reason.db")
    tournament_id = _create_tournament(connection)

    result = archive_or_cancel_tournament(
        connection=connection,
        tournament_id=tournament_id,
        target_status=TournamentStatus.CANCELED.value,
        reason=" ",
        actor="tests",
        operation_group_id="op-safe-empty-reason",
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "reason_required"
    assert TournamentRepository(connection).get(tournament_id)["status"] == "draft"


def test_cancel_draft_tournament_does_not_create_restore_point(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "safe-status-draft-cancel.db")
    tournament_id = _create_tournament(connection)

    result = archive_or_cancel_tournament(
        connection=connection,
        tournament_id=tournament_id,
        target_status=TournamentStatus.CANCELED.value,
        reason="Ошибочный черновик",
        actor="tests",
        operation_group_id="op-safe-draft-cancel",
    )

    assert result["ok"] is True
    assert result["data"]["to_status"] == "canceled"
    assert result["data"]["restore_point_created"] is False
    assert _restore_point_count(connection) == 0
    assert TournamentRepository(connection).get(tournament_id)["status"] == "canceled"


def test_archive_published_tournament_creates_restore_point_and_audit_reason(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "safe-status-published-archive.db")
    tournament_id = _create_tournament(connection)
    _publish_tournament(connection, tournament_id)

    result = archive_or_cancel_tournament(
        connection=connection,
        tournament_id=tournament_id,
        target_status=TournamentStatus.ARCHIVED.value,
        reason="Сезон закрыт",
        actor="tests",
        operation_group_id="op-safe-published-archive",
    )

    assert result["ok"] is True
    assert result["data"]["from_status"] == "published"
    assert result["data"]["to_status"] == "archived"
    assert result["data"]["restore_point_created"] is True
    assert _restore_point_count(connection) == 1
    assert TournamentRepository(connection).get(tournament_id)["status"] == "archived"

    audit_row = connection.execute(
        """
        SELECT reason, operation_group_id
        FROM audit_log
        WHERE entity_type = 'tournament' AND entity_id = ? AND reason = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (str(tournament_id), "Сезон закрыт"),
    ).fetchone()
    assert audit_row is not None
    assert audit_row["operation_group_id"] == "op-safe-published-archive"


def test_archive_or_cancel_rejects_unsupported_target_status(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "safe-status-invalid-target.db")
    tournament_id = _create_tournament(connection)

    result = archive_or_cancel_tournament(
        connection=connection,
        tournament_id=tournament_id,
        target_status=TournamentStatus.PUBLISHED.value,
        reason="Нельзя публиковать через safe wrapper",
        actor="tests",
        operation_group_id="op-safe-invalid-target",
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "unsupported_target_status"
    assert TournamentRepository(connection).get(tournament_id)["status"] == "draft"

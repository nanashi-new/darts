from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.db.database import get_connection
from app.db.repositories import PlayerRepository


pytestmark = pytest.mark.integration


def test_export_profile_backup_creates_valid_copy(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    connection = get_connection()

    # Insert some data
    PlayerRepository(connection).create(
        {
            "last_name": "Export",
            "first_name": "Test",
            "middle_name": None,
            "birth_date": None,
            "gender": None,
            "coach": None,
            "club": None,
            "notes": None,
        }
    )

    from app.services.backup_restore import export_profile_backup

    dest = tmp_path / "backup" / "export.db"
    result = export_profile_backup(connection=connection, destination_path=dest)

    assert result.success is True
    assert result.size_bytes > 0
    assert Path(result.destination_path).exists()

    # Verify exported DB contains the data
    backup_conn = sqlite3.connect(str(dest))
    try:
        row = backup_conn.execute("SELECT last_name FROM players WHERE last_name = 'Export'").fetchone()
        assert row is not None
        assert row[0] == "Export"
    finally:
        backup_conn.close()


def test_import_profile_from_backup_queues_restore(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    connection = get_connection()

    from app.services.backup_restore import export_profile_backup, import_profile_from_backup

    # First export
    dest = tmp_path / "backup.db"
    export_profile_backup(connection=connection, destination_path=dest)

    # Now import from that exported file
    result = import_profile_from_backup(connection=connection, source_path=dest)

    assert result.success is True
    assert "Перезапустите" in result.message

    # Verify pending_action.json was created
    from app.runtime_paths import get_runtime_paths

    paths = get_runtime_paths()
    assert paths.pending_action_path.exists()

    import json

    payload = json.loads(paths.pending_action_path.read_text(encoding="utf-8"))
    assert payload["action"] == "restore_db"
    assert payload["file_path"] == str(dest)


def test_health_check_returns_expected_fields(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    connection = get_connection()

    from app.services.backup_restore import run_health_check

    result = run_health_check(connection=connection)

    assert result.integrity_ok is True
    assert result.integrity_message == "ok"
    assert result.db_size_bytes > 0
    assert result.restore_points_count == 0
    assert result.last_backup_date is None
    assert result.created_at != ""


def test_export_backup_logs_audit_event(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    connection = get_connection()

    from app.services.audit_log import AuditLogService, PROFILE_BACKUP_EXPORTED
    from app.services.backup_restore import export_profile_backup

    dest = tmp_path / "audit_backup.db"
    export_profile_backup(connection=connection, destination_path=dest)

    events = AuditLogService(connection).list_events(event_type=PROFILE_BACKUP_EXPORTED)
    assert len(events) == 1
    assert events[0].event_type == PROFILE_BACKUP_EXPORTED


def test_health_check_on_fresh_db_reports_no_backups(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    connection = get_connection()

    from app.services.backup_restore import run_health_check

    result = run_health_check(connection=connection)

    assert result.last_backup_date is None
    assert result.restore_points_count == 0
    assert result.integrity_ok is True

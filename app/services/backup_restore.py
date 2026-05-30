from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.runtime_paths import get_runtime_paths
from app.services.audit_log import (
    AuditLogService,
    HEALTH_CHECK_RUN,
    PROFILE_BACKUP_EXPORTED,
    PROFILE_BACKUP_IMPORTED,
)
from app.services.restore_points import create_restore_point


@dataclass(frozen=True)
class BackupResult:
    success: bool
    destination_path: str
    size_bytes: int
    created_at: str


@dataclass(frozen=True)
class HealthCheckResult:
    integrity_ok: bool
    integrity_message: str
    db_size_bytes: int
    last_backup_date: str | None
    restore_points_count: int
    created_at: str


@dataclass(frozen=True)
class ImportResult:
    success: bool
    source_path: str
    message: str


def export_profile_backup(
    *,
    connection: sqlite3.Connection,
    destination_path: Path,
) -> BackupResult:
    """Export (backup) the current profile database to the given destination."""
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    backup_conn = sqlite3.connect(str(destination_path))
    try:
        connection.backup(backup_conn)
    finally:
        backup_conn.close()

    size_bytes = os.path.getsize(destination_path)
    created_at = _current_timestamp()

    AuditLogService(connection).log_event(
        PROFILE_BACKUP_EXPORTED,
        "Профиль экспортирован",
        f"Экспортирован в: {destination_path}",
        context={"destination_path": str(destination_path), "size_bytes": size_bytes},
        source="backup_restore",
    )

    return BackupResult(
        success=True,
        destination_path=str(destination_path),
        size_bytes=size_bytes,
        created_at=created_at,
    )


def import_profile_from_backup(
    *,
    connection: sqlite3.Connection,
    source_path: Path,
) -> ImportResult:
    """Validate and queue a profile import from a backup file."""
    if not source_path.exists():
        return ImportResult(
            success=False,
            source_path=str(source_path),
            message="Файл не найден.",
        )

    # Validate integrity of source file
    try:
        check_conn = sqlite3.connect(str(source_path))
        try:
            result = check_conn.execute("PRAGMA integrity_check").fetchone()
            integrity_ok = result is not None and result[0] == "ok"
        finally:
            check_conn.close()
    except Exception:
        return ImportResult(
            success=False,
            source_path=str(source_path),
            message="Файл повреждён или не является базой данных.",
        )

    if not integrity_ok:
        return ImportResult(
            success=False,
            source_path=str(source_path),
            message="Проверка целостности файла не пройдена.",
        )

    # Create restore point of current state before import
    create_restore_point(
        connection=connection,
        title="Перед импортом профиля",
        reason="import_profile",
        source="backup_restore",
    )

    # Queue pending action (similar to queue_restore_from_point)
    paths = get_runtime_paths()
    pending_payload = {
        "action": "restore_db",
        "file_path": str(source_path),
        "requested_at": _current_timestamp(),
    }
    paths.pending_action_path.write_text(
        json.dumps(pending_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    AuditLogService(connection).log_event(
        PROFILE_BACKUP_IMPORTED,
        "Импорт профиля запланирован",
        f"Источник: {source_path}",
        context={"source_path": str(source_path)},
        source="backup_restore",
    )

    return ImportResult(
        success=True,
        source_path=str(source_path),
        message="Импорт запланирован. Перезапустите приложение.",
    )


def run_health_check(
    *,
    connection: sqlite3.Connection,
) -> HealthCheckResult:
    """Run a health check on the profile database."""
    # Integrity check
    try:
        row = connection.execute("PRAGMA integrity_check").fetchone()
        if row is None:
            integrity_ok = False
            integrity_message = "Нет результата проверки"
        else:
            raw_message = row[0] if isinstance(row, (tuple, list)) else row["integrity_check"]
            integrity_ok = raw_message == "ok"
            integrity_message = str(raw_message)
    except Exception as exc:
        integrity_ok = False
        integrity_message = str(exc)

    # DB file size
    paths = get_runtime_paths()
    try:
        db_size_bytes = os.path.getsize(paths.db_path)
    except OSError:
        db_size_bytes = 0

    # Restore points info
    try:
        count_row = connection.execute(
            "SELECT COUNT(*) AS cnt FROM restore_points"
        ).fetchone()
        restore_points_count = int(count_row[0] if isinstance(count_row, (tuple, list)) else count_row["cnt"])
    except Exception:
        restore_points_count = 0

    try:
        last_row = connection.execute(
            "SELECT created_at FROM restore_points ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if last_row is not None:
            last_backup_date = str(
                last_row[0] if isinstance(last_row, (tuple, list)) else last_row["created_at"]
            )
        else:
            last_backup_date = None
    except Exception:
        last_backup_date = None

    created_at = _current_timestamp()

    AuditLogService(connection).log_event(
        HEALTH_CHECK_RUN,
        "Проверка здоровья выполнена",
        f"Целостность: {'ОК' if integrity_ok else integrity_message}",
        context={
            "integrity_ok": integrity_ok,
            "db_size_bytes": db_size_bytes,
            "restore_points_count": restore_points_count,
        },
        source="backup_restore",
    )

    return HealthCheckResult(
        integrity_ok=integrity_ok,
        integrity_message=integrity_message,
        db_size_bytes=db_size_bytes,
        last_backup_date=last_backup_date,
        restore_points_count=restore_points_count,
        created_at=created_at,
    )


def create_quick_backup() -> Path:
    """Create a quick backup of the current profile database.

    Gets connection and paths automatically. Stores the backup under
    restore_points_dir with a timestamped filename.

    Returns the path of the created backup file.
    """
    from app.db.database import get_connection

    connection = get_connection()
    paths = get_runtime_paths()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    destination = paths.restore_points_dir / f"quick_backup_{timestamp}.db"
    destination.parent.mkdir(parents=True, exist_ok=True)

    backup_conn = sqlite3.connect(str(destination))
    try:
        connection.backup(backup_conn)
    finally:
        backup_conn.close()

    return destination


def _current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

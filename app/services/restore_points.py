from __future__ import annotations

import json
import shutil
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.db.repositories import RestorePointRepository
from app.runtime_paths import get_runtime_paths
from app.services.audit_log import (
    AuditLogService,
    PROFILE_RESET_REQUESTED,
    PROFILE_RESTORE_REQUESTED,
    PROFILE_RESTORED,
    RESTORE_POINT_CREATED,
)


@dataclass(frozen=True)
class RestorePointRecord:
    id: int
    title: str
    reason: str
    file_path: str
    source: str | None
    operation_group_id: str | None
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def create_restore_point(
    *,
    connection,
    title: str,
    reason: str,
    source: str,
    operation_group_id: str | None = None,
) -> RestorePointRecord:
    paths = get_runtime_paths()
    timestamp = _timestamp_token()
    safe_title = _slugify(title) or "restore-point"
    backup_path = paths.restore_points_dir / f"{timestamp}_{safe_title}.db"
    _backup_connection(connection, backup_path)
    repository = RestorePointRepository(connection)
    restore_point_id = repository.create(
        {
            "title": title,
            "reason": reason,
            "file_path": str(backup_path),
            "source": source,
            "operation_group_id": operation_group_id,
            "created_at": _current_timestamp(),
        }
    )
    record = _to_record(
        repository.get(restore_point_id)
        or {
            "id": restore_point_id,
            "title": title,
            "reason": reason,
            "file_path": str(backup_path),
            "source": source,
            "operation_group_id": operation_group_id,
            "created_at": _current_timestamp(),
        }
    )
    AuditLogService(connection).log_event(
        RESTORE_POINT_CREATED,
        "Создан restore point",
        f"{title}: {backup_path.name}",
        context=record.to_dict(),
        source=source,
        operation_group_id=operation_group_id,
    )
    return record


def list_restore_points(*, connection) -> list[RestorePointRecord]:
    repository = RestorePointRepository(connection)
    return [_to_record(item) for item in repository.list()]


def queue_restore_from_point(
    *,
    connection,
    restore_point_id: int,
    source: str,
    operation_group_id: str | None = None,
) -> Path:
    repository = RestorePointRepository(connection)
    row = repository.get(restore_point_id)
    if row is None:
        raise ValueError("Restore point not found.")
    record = _to_record(row)
    pending_payload = {
        "action": "restore_db",
        "restore_point_id": record.id,
        "file_path": record.file_path,
        "requested_at": _current_timestamp(),
    }
    pending_path = _write_pending_action(pending_payload)
    AuditLogService(connection).log_event(
        PROFILE_RESTORE_REQUESTED,
        "Запрошено восстановление профиля",
        f"Restore point #{record.id}",
        context={"restore_point_id": record.id, "file_path": record.file_path},
        source=source,
        operation_group_id=operation_group_id,
    )
    return pending_path


def queue_safe_profile_reset(
    *,
    connection,
    source: str,
    operation_group_id: str | None = None,
) -> Path:
    create_restore_point(
        connection=connection,
        title="Before safe profile reset",
        reason="safe_profile_reset",
        source=source,
        operation_group_id=operation_group_id,
    )
    pending_payload = {
        "action": "reset_profile",
        "requested_at": _current_timestamp(),
    }
    pending_path = _write_pending_action(pending_payload)
    AuditLogService(connection).log_event(
        PROFILE_RESET_REQUESTED,
        "Запрошен безопасный reset профиля",
        "Reset будет выполнен при следующем запуске.",
        context={"pending_action_path": str(pending_path)},
        source=source,
        operation_group_id=operation_group_id,
    )
    return pending_path


def process_pending_profile_action() -> dict[str, Any] | None:
    paths = get_runtime_paths()
    pending_path = paths.pending_action_path
    if not pending_path.exists():
        return None
    try:
        payload = json.loads(pending_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pending_path.unlink(missing_ok=True)
        return None
    if not isinstance(payload, dict):
        pending_path.unlink(missing_ok=True)
        return None

    action = str(payload.get("action") or "").strip()
    if action == "restore_db":
        result = _apply_restore_action(paths=paths, payload=payload)
    elif action == "reset_profile":
        result = _apply_reset_action(paths=paths)
    else:
        result = {"action": action, "status": "ignored"}
    pending_path.unlink(missing_ok=True)
    return result


def _apply_restore_action(*, paths, payload: dict[str, Any]) -> dict[str, Any]:
    source_path = Path(str(payload.get("file_path") or ""))
    if not source_path.exists():
        return {"action": "restore_db", "status": "missing_restore_point"}
    paths.db_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, paths.db_path)
    from app.db.database import get_connection

    connection = get_connection(paths.db_path)
    try:
        AuditLogService(connection).log_event(
            PROFILE_RESTORED,
            "Профиль восстановлен",
            f"Источник: {source_path.name}",
            context={"file_path": str(source_path)},
            source="startup_restore",
        )
    finally:
        connection.close()
    return {"action": "restore_db", "status": "applied", "file_path": str(source_path)}


def _apply_reset_action(*, paths) -> dict[str, Any]:
    timestamp = _timestamp_token()
    backup_dir = paths.profile_backups_dir / f"profile_reset_{timestamp}"
    if paths.profile_root.exists():
        backup_dir.parent.mkdir(parents=True, exist_ok=True)
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        shutil.copytree(paths.profile_root, backup_dir)
        for child in list(paths.profile_root.iterdir()):
            if child.name == paths.pending_action_path.name:
                continue
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)
    paths.ensure_exists()
    from app.db.database import get_connection

    connection = get_connection(paths.db_path)
    try:
        AuditLogService(connection).log_event(
            PROFILE_RESTORED,
            "Профиль сброшен",
            "Создан чистый профиль после safe reset.",
            context={"backup_dir": str(backup_dir)},
            source="startup_reset",
        )
    finally:
        connection.close()
    return {"action": "reset_profile", "status": "applied", "backup_dir": str(backup_dir)}


def _write_pending_action(payload: dict[str, Any]) -> Path:
    paths = get_runtime_paths()
    paths.pending_action_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return paths.pending_action_path


def _backup_connection(connection: sqlite3.Connection, destination_path: Path) -> None:
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    backup_connection = sqlite3.connect(str(destination_path))
    try:
        connection.backup(backup_connection)
    finally:
        backup_connection.close()


def _to_record(row: dict[str, Any]) -> RestorePointRecord:
    return RestorePointRecord(
        id=int(row["id"]),
        title=str(row["title"]),
        reason=str(row["reason"]),
        file_path=str(row["file_path"]),
        source=str(row["source"]) if row.get("source") is not None else None,
        operation_group_id=(
            str(row["operation_group_id"])
            if row.get("operation_group_id") is not None
            else None
        ),
        created_at=str(row["created_at"]),
    )


def _slugify(value: str) -> str:
    normalized = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    return "-".join(part for part in normalized.split("-") if part)


def _current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _timestamp_token() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

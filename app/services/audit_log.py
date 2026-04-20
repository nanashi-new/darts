from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from app.db.database import get_connection

IMPORT_FILE = "IMPORT_FILE"
IMPORT_FOLDER = "IMPORT_FOLDER"
IMPORT_REPORT = "IMPORT_REPORT"
RATING_SNAPSHOT_CREATED = "RATING_SNAPSHOT_CREATED"
LEAGUE_TRANSFER_CREATED = "LEAGUE_TRANSFER_CREATED"
NOTE_CREATED = "NOTE_CREATED"
TRAINING_ENTRY_CREATED = "TRAINING_ENTRY_CREATED"
RESTORE_POINT_CREATED = "RESTORE_POINT_CREATED"
PROFILE_RESET_REQUESTED = "PROFILE_RESET_REQUESTED"
PROFILE_RESTORE_REQUESTED = "PROFILE_RESTORE_REQUESTED"
PROFILE_RESTORED = "PROFILE_RESTORED"
SELF_CHECK_RUN = "SELF_CHECK_RUN"
DIAGNOSTIC_BUNDLE_EXPORTED = "DIAGNOSTIC_BUNDLE_EXPORTED"
RECALC_TOURNAMENT = "RECALC_TOURNAMENT"
RECALC_ALL = "RECALC_ALL"
EXPORT_FILE = "EXPORT_FILE"
EXPORT_BATCH = "EXPORT_BATCH"
ERROR = "ERROR"
MERGE_PLAYERS = "MERGE_PLAYERS"
TOURNAMENT_CREATED = "tournament_created"
TOURNAMENT_UPDATED = "tournament_updated"
TOURNAMENT_PUBLISHED = "tournament_published"
TOURNAMENT_CORRECTED = "tournament_corrected"
TOURNAMENT_DELETED = "tournament_deleted"

EVENT_TYPES = [
    IMPORT_FILE,
    IMPORT_FOLDER,
    IMPORT_REPORT,
    RATING_SNAPSHOT_CREATED,
    LEAGUE_TRANSFER_CREATED,
    NOTE_CREATED,
    TRAINING_ENTRY_CREATED,
    RESTORE_POINT_CREATED,
    PROFILE_RESET_REQUESTED,
    PROFILE_RESTORE_REQUESTED,
    PROFILE_RESTORED,
    SELF_CHECK_RUN,
    DIAGNOSTIC_BUNDLE_EXPORTED,
    RECALC_TOURNAMENT,
    RECALC_ALL,
    EXPORT_FILE,
    EXPORT_BATCH,
    MERGE_PLAYERS,
    ERROR,
    TOURNAMENT_CREATED,
    TOURNAMENT_UPDATED,
    TOURNAMENT_PUBLISHED,
    TOURNAMENT_CORRECTED,
    TOURNAMENT_DELETED,
]


@dataclass(frozen=True)
class AuditEvent:
    id: int
    event_type: str
    title: str
    details: str
    level: str
    context: dict[str, object]
    entity_type: str | None
    entity_id: str | None
    reason: str | None
    old_value_json: str | None
    new_value_json: str | None
    source: str | None
    operation_group_id: str | None
    created_at: str


class AuditLogService:
    def __init__(self, connection: sqlite3.Connection | None = None) -> None:
        self._connection = connection or get_connection()

    def log_event(
        self,
        event_type: str,
        title: str,
        details: str,
        level: str = "info",
        context: dict[str, object] | None = None,
        *,
        entity_type: str | None = None,
        entity_id: str | None = None,
        reason: str | None = None,
        old_value_json: str | None = None,
        new_value_json: str | None = None,
        source: str | None = None,
        operation_group_id: str | None = None,
    ) -> int:
        context_json = json.dumps(context or {}, ensure_ascii=False)
        with self._connection:
            cursor = self._connection.execute(
                """
                INSERT INTO audit_log (
                    event_type,
                    title,
                    details,
                    level,
                    context_json,
                    entity_type,
                    entity_id,
                    reason,
                    old_value_json,
                    new_value_json,
                    source,
                    operation_group_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_type,
                    title,
                    details,
                    level,
                    context_json,
                    entity_type,
                    entity_id,
                    reason,
                    old_value_json,
                    new_value_json,
                    source,
                    operation_group_id,
                ),
            )
        return _require_int_id(cursor.lastrowid, "SQLite cursor has no lastrowid after INSERT")

    def list_events(self, event_type: str | None = None, query: str = "") -> list[AuditEvent]:
        clauses: list[str] = []
        params: list[object] = []

        if event_type:
            clauses.append("event_type = ?")
            params.append(event_type)

        if query.strip():
            clauses.append("(title LIKE ? OR details LIKE ?)")
            like = f"%{query.strip()}%"
            params.extend([like, like])

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._connection.execute(
            f"""
            SELECT
                id,
                event_type,
                title,
                details,
                level,
                context_json,
                entity_type,
                entity_id,
                reason,
                old_value_json,
                new_value_json,
                source,
                operation_group_id,
                created_at
            FROM audit_log
            {where_sql}
            ORDER BY id DESC
            """,
            params,
        ).fetchall()
        return [self._row_to_event(row) for row in rows]

    def export_txt(self, path: str | Path, event_type: str | None = None, query: str = "") -> Path:
        output_path = Path(path)
        events = self.list_events(event_type=event_type, query=query)
        lines: list[str] = []
        for event in events:
            lines.append(
                f"[{event.created_at}] {event.level.upper()} {event.event_type} | {event.title} | {event.details}"
            )
        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path

    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> AuditEvent:
        try:
            context = json.loads(row["context_json"] or "{}")
        except json.JSONDecodeError:
            context = {}
        if not isinstance(context, dict):
            context = {}

        return AuditEvent(
            id=_require_int_id(row["id"], "audit_log.id is NULL"),
            event_type=str(row["event_type"]),
            title=str(row["title"]),
            details=str(row["details"] or ""),
            level=str(row["level"] or "info"),
            context=context,
            entity_type=str(row["entity_type"]) if row["entity_type"] is not None else None,
            entity_id=str(row["entity_id"]) if row["entity_id"] is not None else None,
            reason=str(row["reason"]) if row["reason"] is not None else None,
            old_value_json=str(row["old_value_json"]) if row["old_value_json"] is not None else None,
            new_value_json=str(row["new_value_json"]) if row["new_value_json"] is not None else None,
            source=str(row["source"]) if row["source"] is not None else None,
            operation_group_id=str(row["operation_group_id"]) if row["operation_group_id"] is not None else None,
            created_at=str(row["created_at"]),
        )


def _require_int_id(value: object | None, null_message: str) -> int:
    if value is None:
        raise ValueError(null_message)
    if isinstance(value, int):
        return value
    return int(str(value))

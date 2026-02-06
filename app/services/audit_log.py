from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from app.db.database import get_connection

IMPORT_FILE = "IMPORT_FILE"
IMPORT_FOLDER = "IMPORT_FOLDER"
RECALC_TOURNAMENT = "RECALC_TOURNAMENT"
RECALC_ALL = "RECALC_ALL"
EXPORT_FILE = "EXPORT_FILE"
EXPORT_BATCH = "EXPORT_BATCH"
ERROR = "ERROR"

EVENT_TYPES = [
    IMPORT_FILE,
    IMPORT_FOLDER,
    RECALC_TOURNAMENT,
    RECALC_ALL,
    EXPORT_FILE,
    EXPORT_BATCH,
    ERROR,
]


@dataclass(frozen=True)
class AuditEvent:
    id: int
    event_type: str
    title: str
    details: str
    level: str
    context: dict[str, object]
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
    ) -> int:
        context_json = json.dumps(context or {}, ensure_ascii=False)
        with self._connection:
            cursor = self._connection.execute(
                """
                INSERT INTO audit_log (event_type, title, details, level, context_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (event_type, title, details, level, context_json),
            )
        return int(cursor.lastrowid)

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
            SELECT id, event_type, title, details, level, context_json, created_at
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
            id=int(row["id"]),
            event_type=str(row["event_type"]),
            title=str(row["title"]),
            details=str(row["details"] or ""),
            level=str(row["level"] or "info"),
            context=context,
            created_at=str(row["created_at"]),
        )

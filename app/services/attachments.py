"""Attachment management service.

Note on orphan records: attachments uses (entity_type, entity_id) as TEXT columns
without foreign keys to parent tables. If an entity (e.g. player) is deleted, its
attachment records become orphaned. This is an acceptable trade-off for a local desktop
app where data volume is small. Orphan cleanup can be added as a periodic maintenance
task or handled at the application level in entity delete paths if needed.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class AttachmentRecord:
    id: int
    entity_type: str
    entity_id: str
    file_path: str
    file_name: str
    description: str | None
    file_size: int | None
    created_at: str


def create_attachment(
    connection: sqlite3.Connection,
    entity_type: str,
    entity_id: str,
    file_path: str,
    file_name: str,
    description: str | None = None,
    file_size: int | None = None,
) -> int:
    """Create an attachment record and return its ID."""
    cursor = connection.execute(
        """
        INSERT INTO attachments (entity_type, entity_id, file_path, file_name, description, file_size)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (entity_type, entity_id, file_path, file_name, description, file_size),
    )
    connection.commit()
    return int(cursor.lastrowid)  # type: ignore[arg-type]


def list_entity_attachments(connection: sqlite3.Connection, entity_type: str, entity_id: str) -> list[AttachmentRecord]:
    """List all attachments for an entity."""
    rows = connection.execute(
        """
        SELECT id, entity_type, entity_id, file_path, file_name, description, file_size, created_at
        FROM attachments
        WHERE entity_type = ? AND entity_id = ?
        ORDER BY created_at DESC
        """,
        (entity_type, entity_id),
    ).fetchall()
    return [
        AttachmentRecord(
            id=row[0], entity_type=row[1], entity_id=row[2],
            file_path=row[3], file_name=row[4], description=row[5],
            file_size=row[6], created_at=row[7],
        )
        for row in rows
    ]


def delete_attachment(connection: sqlite3.Connection, attachment_id: int) -> None:
    """Delete an attachment record."""
    connection.execute("DELETE FROM attachments WHERE id = ?", (attachment_id,))
    connection.commit()

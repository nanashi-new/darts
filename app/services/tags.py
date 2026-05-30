"""Tag management service.

Note on orphan records: entity_tags uses (entity_type, entity_id) as TEXT columns
without foreign keys to parent tables. If an entity (e.g. player) is deleted, its
tag assignments become orphaned. This is an acceptable trade-off for a local desktop
app where data volume is small. Orphan cleanup can be added as a periodic maintenance
task or handled at the application level in entity delete paths if needed.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class TagRecord:
    id: int
    name: str
    color: str | None
    created_at: str


def create_tag(connection: sqlite3.Connection, name: str, color: str | None = None) -> int:
    """Create a new tag and return its ID."""
    cursor = connection.execute(
        "INSERT INTO tags (name, color) VALUES (?, ?)",
        (name.strip(), color),
    )
    connection.commit()
    return int(cursor.lastrowid)  # type: ignore[arg-type]


def list_tags(connection: sqlite3.Connection) -> list[TagRecord]:
    """List all tags."""
    rows = connection.execute("SELECT id, name, color, created_at FROM tags ORDER BY name").fetchall()
    return [TagRecord(id=row[0], name=row[1], color=row[2], created_at=row[3]) for row in rows]


def assign_tag(connection: sqlite3.Connection, tag_id: int, entity_type: str, entity_id: str) -> None:
    """Assign a tag to an entity."""
    connection.execute(
        "INSERT OR IGNORE INTO entity_tags (tag_id, entity_type, entity_id) VALUES (?, ?, ?)",
        (tag_id, entity_type, entity_id),
    )
    connection.commit()


def remove_tag_assignment(connection: sqlite3.Connection, tag_id: int, entity_type: str, entity_id: str) -> None:
    """Remove a tag assignment from an entity."""
    connection.execute(
        "DELETE FROM entity_tags WHERE tag_id = ? AND entity_type = ? AND entity_id = ?",
        (tag_id, entity_type, entity_id),
    )
    connection.commit()


def list_entity_tags(connection: sqlite3.Connection, entity_type: str, entity_id: str) -> list[TagRecord]:
    """List all tags assigned to an entity."""
    rows = connection.execute(
        """
        SELECT t.id, t.name, t.color, t.created_at
        FROM tags t
        JOIN entity_tags et ON et.tag_id = t.id
        WHERE et.entity_type = ? AND et.entity_id = ?
        ORDER BY t.name
        """,
        (entity_type, entity_id),
    ).fetchall()
    return [TagRecord(id=row[0], name=row[1], color=row[2], created_at=row[3]) for row in rows]


def delete_tag(connection: sqlite3.Connection, tag_id: int) -> None:
    """Delete a tag and all its assignments."""
    connection.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
    connection.commit()

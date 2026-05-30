"""Custom fields management service."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class CustomFieldRecord:
    id: int
    name: str
    field_type: str
    options_json: str | None
    sort_order: int
    is_active: int
    created_at: str


@dataclass(frozen=True)
class CustomFieldValueRecord:
    id: int
    field_id: int
    field_name: str
    field_type: str
    value: str | None
    created_at: str


def create_custom_field(
    connection: sqlite3.Connection,
    name: str,
    field_type: str,
    options_json: str | None = None,
) -> int:
    """Create a custom field definition and return its ID."""
    cursor = connection.execute(
        "INSERT INTO custom_fields (name, field_type, options_json) VALUES (?, ?, ?)",
        (name.strip(), field_type, options_json),
    )
    connection.commit()
    return int(cursor.lastrowid)  # type: ignore[arg-type]


def list_custom_fields(connection: sqlite3.Connection, active_only: bool = True) -> list[CustomFieldRecord]:
    """List custom field definitions."""
    query = "SELECT id, name, field_type, options_json, sort_order, is_active, created_at FROM custom_fields"
    if active_only:
        query += " WHERE is_active = 1"
    query += " ORDER BY sort_order, name"
    rows = connection.execute(query).fetchall()
    return [
        CustomFieldRecord(
            id=row[0], name=row[1], field_type=row[2], options_json=row[3],
            sort_order=row[4], is_active=row[5], created_at=row[6],
        )
        for row in rows
    ]


def set_field_value(connection: sqlite3.Connection, custom_field_id: int, player_id: int, value: str | None) -> int:
    """Set a custom field value for a player. Returns the value record ID."""
    cursor = connection.execute(
        """
        INSERT INTO custom_field_values (custom_field_id, player_id, value)
        VALUES (?, ?, ?)
        ON CONFLICT(custom_field_id, player_id) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
        """,
        (custom_field_id, player_id, value),
    )
    connection.commit()
    return int(cursor.lastrowid)  # type: ignore[arg-type]


def get_player_custom_values(connection: sqlite3.Connection, player_id: int) -> list[CustomFieldValueRecord]:
    """Get all custom field values for a player."""
    rows = connection.execute(
        """
        SELECT cfv.id, cfv.custom_field_id, cf.name, cf.field_type, cfv.value, cfv.created_at
        FROM custom_field_values cfv
        JOIN custom_fields cf ON cf.id = cfv.custom_field_id
        WHERE cfv.player_id = ? AND cf.is_active = 1
        ORDER BY cf.sort_order, cf.name
        """,
        (player_id,),
    ).fetchall()
    return [
        CustomFieldValueRecord(
            id=row[0], field_id=row[1], field_name=row[2],
            field_type=row[3], value=row[4], created_at=row[5],
        )
        for row in rows
    ]


def delete_custom_field(connection: sqlite3.Connection, field_id: int) -> None:
    """Delete a custom field and all its values."""
    connection.execute("DELETE FROM custom_fields WHERE id = ?", (field_id,))
    connection.commit()

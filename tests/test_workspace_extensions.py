"""Tests for workspace extensions: tags, attachments, custom fields."""
from __future__ import annotations

import sqlite3

import pytest

from app.db.database import get_connection


def test_tag_crud(tmp_path: object) -> None:
    from app.services.tags import (
        assign_tag,
        create_tag,
        delete_tag,
        list_entity_tags,
        list_tags,
        remove_tag_assignment,
    )

    connection = get_connection(str(tmp_path) + "/ws.db")  # type: ignore[arg-type]

    # Create tags
    tag1_id = create_tag(connection, "Important", "#FF0000")
    tag2_id = create_tag(connection, "VIP", "#00FF00")

    # List tags
    tags = list_tags(connection)
    assert len(tags) == 2
    assert tags[0].name == "Important"  # alphabetical
    assert tags[1].name == "VIP"

    # Assign tags to entity
    assign_tag(connection, tag1_id, "player", "1")
    assign_tag(connection, tag2_id, "player", "1")

    # List entity tags
    player_tags = list_entity_tags(connection, "player", "1")
    assert len(player_tags) == 2

    # Remove assignment
    remove_tag_assignment(connection, tag1_id, "player", "1")
    player_tags = list_entity_tags(connection, "player", "1")
    assert len(player_tags) == 1
    assert player_tags[0].name == "VIP"

    # Delete tag
    delete_tag(connection, tag2_id)
    player_tags = list_entity_tags(connection, "player", "1")
    assert len(player_tags) == 0


def test_attachment_crud(tmp_path: object) -> None:
    from app.services.attachments import create_attachment, delete_attachment, list_entity_attachments

    connection = get_connection(str(tmp_path) + "/ws.db")  # type: ignore[arg-type]

    att_id = create_attachment(connection, "player", "1", "/path/to/file.pdf", "file.pdf", "Test doc", 1024)

    atts = list_entity_attachments(connection, "player", "1")
    assert len(atts) == 1
    assert atts[0].file_name == "file.pdf"
    assert atts[0].file_size == 1024

    delete_attachment(connection, att_id)
    atts = list_entity_attachments(connection, "player", "1")
    assert len(atts) == 0


def test_custom_field_crud(tmp_path: object) -> None:
    from app.db.repositories import PlayerRepository
    from app.services.custom_fields import (
        create_custom_field,
        delete_custom_field,
        get_player_custom_values,
        list_custom_fields,
        set_field_value,
    )

    connection = get_connection(str(tmp_path) + "/ws.db")  # type: ignore[arg-type]

    # Need a player
    player_id = PlayerRepository(connection).create(
        {
            "last_name": "Test",
            "first_name": "User",
            "middle_name": None,
            "birth_date": None,
            "gender": None,
            "coach": None,
            "club": None,
            "notes": None,
        }
    )

    # Create fields
    field1_id = create_custom_field(connection, "Height", "number")
    field2_id = create_custom_field(connection, "Phone", "text")

    fields = list_custom_fields(connection)
    assert len(fields) == 2

    # Set values
    set_field_value(connection, field1_id, player_id, "175")
    set_field_value(connection, field2_id, player_id, "+7-999-123-4567")

    values = get_player_custom_values(connection, player_id)
    assert len(values) == 2
    assert any(v.field_name == "Height" and v.value == "175" for v in values)
    assert any(v.field_name == "Phone" and v.value == "+7-999-123-4567" for v in values)

    # Update value
    set_field_value(connection, field1_id, player_id, "180")
    values = get_player_custom_values(connection, player_id)
    assert any(v.field_name == "Height" and v.value == "180" for v in values)

    # Delete field
    delete_custom_field(connection, field1_id)
    values = get_player_custom_values(connection, player_id)
    assert len(values) == 1


def test_schema_creates_new_tables(tmp_path: object) -> None:
    connection = get_connection(str(tmp_path) + "/ws.db")  # type: ignore[arg-type]
    tables = [
        row[0]
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    ]
    assert "tags" in tables
    assert "entity_tags" in tables
    assert "attachments" in tables
    assert "custom_fields" in tables
    assert "custom_field_values" in tables


def test_tag_duplicate_name_raises(tmp_path: object) -> None:
    from app.services.tags import create_tag

    connection = get_connection(str(tmp_path) + "/ws.db")  # type: ignore[arg-type]
    create_tag(connection, "Unique", "#000")
    with pytest.raises(sqlite3.IntegrityError):
        create_tag(connection, "Unique", "#FFF")


def test_assign_tag_idempotent(tmp_path: object) -> None:
    from app.services.tags import assign_tag, create_tag, list_entity_tags

    connection = get_connection(str(tmp_path) + "/ws.db")  # type: ignore[arg-type]
    tag_id = create_tag(connection, "Repeat")
    assign_tag(connection, tag_id, "player", "1")
    assign_tag(connection, tag_id, "player", "1")  # should not raise
    tags = list_entity_tags(connection, "player", "1")
    assert len(tags) == 1

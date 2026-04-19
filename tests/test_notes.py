from __future__ import annotations

import pytest

from app.db.database import get_connection
from app.db.repositories import PlayerRepository
from app.services.audit_log import AuditLogService


pytestmark = pytest.mark.integration


def test_create_player_note_and_list_entity_notes(tmp_path) -> None:
    connection = get_connection(tmp_path / "notes-player.db")
    players = PlayerRepository(connection)
    player_id = players.create(
        {
            "last_name": "Note",
            "first_name": "Player",
            "middle_name": None,
            "birth_date": None,
            "gender": None,
            "coach": None,
            "club": None,
            "notes": None,
        }
    )

    from app.services.notes import create_note, list_entity_notes

    note_id = create_note(
        connection=connection,
        entity_type="player",
        entity_id=str(player_id),
        note_type="player_note",
        visibility="internal_service",
        title="Needs follow-up",
        body="Discuss next tournament plan.",
        priority="high",
        author="tests",
        is_pinned=True,
    )

    notes = list_entity_notes(connection=connection, entity_type="player", entity_id=str(player_id))
    assert note_id > 0
    assert len(notes) == 1
    assert notes[0].title == "Needs follow-up"
    assert notes[0].body == "Discuss next tournament plan."
    assert notes[0].visibility == "internal_service"
    assert notes[0].is_pinned is True
    assert notes[0].entity_type == "player"
    assert notes[0].entity_id == str(player_id)

    audit = AuditLogService(connection).list_events(query="Needs follow-up")
    assert audit


def test_list_entity_notes_supports_generic_entities_filters_and_ordering(tmp_path) -> None:
    connection = get_connection(tmp_path / "notes-generic.db")
    players = PlayerRepository(connection)
    player_id = players.create(
        {
            "last_name": "Filter",
            "first_name": "Case",
            "middle_name": None,
            "birth_date": None,
            "gender": None,
            "coach": None,
            "club": None,
            "notes": None,
        }
    )

    from app.services.notes import create_note, list_entity_notes

    create_note(
        connection=connection,
        entity_type="tournament",
        entity_id="101",
        note_type="tournament_note",
        visibility="internal_service",
        title="Tournament logistics",
        body="Need to confirm venue access.",
        priority="normal",
        author="tests",
        is_pinned=False,
    )
    create_note(
        connection=connection,
        entity_type="tournament",
        entity_id="101",
        note_type="follow_up",
        visibility="follow_up",
        title="Top priority follow-up",
        body="Follow up with the venue manager.",
        priority="high",
        author="tests",
        is_pinned=True,
    )
    create_note(
        connection=connection,
        entity_type="league",
        entity_id="PREMIER",
        note_type="league_note",
        visibility="internal_service",
        title="League memo",
        body="Premier league calendar draft.",
        priority="low",
        author="tests",
    )
    create_note(
        connection=connection,
        entity_type="player",
        entity_id=str(player_id),
        note_type="coach_note",
        visibility="coach_only",
        title="Coach focus",
        body="Player needs extra doubles practice.",
        priority="normal",
        author="coach",
    )

    tournament_notes = list_entity_notes(
        connection=connection,
        entity_type="tournament",
        entity_id="101",
    )
    assert [note.title for note in tournament_notes] == [
        "Top priority follow-up",
        "Tournament logistics",
    ]

    filtered_type = list_entity_notes(
        connection=connection,
        entity_type="tournament",
        entity_id="101",
        note_types=["follow_up"],
    )
    assert [note.title for note in filtered_type] == ["Top priority follow-up"]

    filtered_visibility = list_entity_notes(
        connection=connection,
        entity_type="player",
        entity_id=str(player_id),
        visibilities=["coach_only"],
    )
    assert [note.title for note in filtered_visibility] == ["Coach focus"]

    query_notes = list_entity_notes(
        connection=connection,
        entity_type="league",
        entity_id="PREMIER",
        query="calendar",
    )
    assert [note.title for note in query_notes] == ["League memo"]

from __future__ import annotations

import pytest

from app.db.database import get_connection
from app.db.repositories import PlayerRepository, TournamentRepository


pytestmark = pytest.mark.integration


def test_create_and_list_training_entries(tmp_path) -> None:
    connection = get_connection(tmp_path / "training-journal.db")
    player_id = PlayerRepository(connection).create(
        {
            "last_name": "Training",
            "first_name": "Case",
            "middle_name": None,
            "birth_date": None,
            "gender": None,
            "coach": "Coach One",
            "club": None,
            "notes": None,
        }
    )
    tournament_id = TournamentRepository(connection).create(
        {
            "name": "Training Cup",
            "date": "2026-05-01",
            "category_code": "U18",
            "league_code": None,
            "source_files": "[]",
        }
    )

    from app.services.training_journal import (
        create_training_entry,
        list_player_training_entries,
        list_training_entries,
    )

    entry_id = create_training_entry(
        connection=connection,
        player_id=player_id,
        coach_name="Coach One",
        training_date="2026-05-02",
        session_type="match_prep",
        summary="Focused doubles session",
        goals="Stabilize checkout rhythm",
        metrics={"doubles_hit": 18},
        related_tournament_id=tournament_id,
        next_action="Repeat on Friday",
    )

    player_entries = list_player_training_entries(connection=connection, player_id=player_id)
    all_entries = list_training_entries(connection=connection, query="doubles")

    assert entry_id > 0
    assert len(player_entries) == 1
    assert player_entries[0].summary == "Focused doubles session"
    assert player_entries[0].coach_name == "Coach One"
    assert player_entries[0].metrics["doubles_hit"] == 18
    assert len(all_entries) == 1

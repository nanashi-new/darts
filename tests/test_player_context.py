from __future__ import annotations

import pytest

from app.db.database import get_connection
from app.db.repositories import PlayerRepository, ResultRepository, TournamentRepository
from app.services.tournament_lifecycle import transition_tournament_status


pytestmark = pytest.mark.integration


def test_list_latest_player_rating_states_returns_latest_scope_rows(tmp_path) -> None:
    connection = get_connection(tmp_path / "player-context-rating-states.db")
    players = PlayerRepository(connection)
    tournaments = TournamentRepository(connection)
    results = ResultRepository(connection)
    player_id = players.create(
        {
            "last_name": "State",
            "first_name": "Player",
            "middle_name": None,
            "birth_date": None,
            "gender": None,
            "coach": None,
            "club": None,
            "notes": None,
        }
    )
    tournament_id = tournaments.create(
        {
            "name": "State Cup",
            "date": "2026-04-27",
            "category_code": "U18",
            "league_code": "PREMIER",
            "is_adult_mode": 0,
            "source_files": "[]",
            "status": "draft",
            "has_draft_changes": 1,
        }
    )
    results.create(
        {
            "tournament_id": tournament_id,
            "player_id": player_id,
            "place": 1,
            "score_set": 0,
            "score_sector20": 0,
            "score_big_round": 0,
            "rank_set": None,
            "rank_sector20": None,
            "rank_big_round": None,
            "points_classification": 0,
            "points_place": 120,
            "points_total": 120,
            "calc_version": "tests",
        }
    )
    for target in ("review", "confirmed", "published"):
        assert transition_tournament_status(
            connection=connection,
            tournament_id=tournament_id,
            to_status=target,
            context={"actor": "tests", "operation_group_id": "op-player-context"},
        )["ok"] is True

    from app.services.rating_snapshot import list_latest_player_rating_states

    rows = list_latest_player_rating_states(connection, player_id=player_id)

    scope_pairs = {(row.scope_type, row.scope_key) for row in rows}
    assert ("category", "U18") in scope_pairs
    assert ("league", "PREMIER") in scope_pairs


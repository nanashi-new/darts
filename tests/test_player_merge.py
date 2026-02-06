from pathlib import Path

from app.db.database import get_connection
from app.db.repositories import PlayerRepository, ResultRepository, TournamentRepository
from app.services.player_merge import MERGE_PLAYERS, PlayerMergeService


def test_merge_players_moves_results_removes_duplicate_and_logs_event(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "app.db")
    players = PlayerRepository(connection)
    tournaments = TournamentRepository(connection)
    results = ResultRepository(connection)
    merge_service = PlayerMergeService(connection)

    primary_id = players.create(
        {
            "last_name": "Иванов",
            "first_name": "Иван",
            "middle_name": "Иванович",
            "birth_date": "2000-01-01",
            "gender": "M",
            "coach": None,
            "club": None,
            "notes": None,
        }
    )
    duplicate_id = players.create(
        {
            "last_name": "иванов",
            "first_name": "иван",
            "middle_name": "иванович",
            "birth_date": "2000-01-01",
            "gender": "M",
            "coach": "Coach 1",
            "club": "Club 1",
            "notes": "note",
        }
    )

    tournament_primary = tournaments.create(
        {
            "name": "Cup A",
            "date": "2025-01-01",
            "category_code": "A",
            "league_code": None,
            "source_files": "[]",
        }
    )
    tournament_duplicate = tournaments.create(
        {
            "name": "Cup B",
            "date": "2025-02-01",
            "category_code": "A",
            "league_code": None,
            "source_files": "[]",
        }
    )

    results.create(
        {
            "tournament_id": tournament_primary,
            "player_id": primary_id,
            "place": 1,
            "score_set": 80,
            "score_sector20": 20,
            "score_big_round": 40,
            "rank_set": "A",
            "rank_sector20": "A",
            "rank_big_round": "A",
            "points_classification": 50,
            "points_place": 100,
            "points_total": 150,
            "calc_version": "v1",
        }
    )
    results.create(
        {
            "tournament_id": tournament_duplicate,
            "player_id": duplicate_id,
            "place": 2,
            "score_set": 70,
            "score_sector20": 15,
            "score_big_round": 30,
            "rank_set": "B",
            "rank_sector20": "B",
            "rank_big_round": "B",
            "points_classification": 40,
            "points_place": 80,
            "points_total": 120,
            "calc_version": "v1",
        }
    )

    groups = merge_service.find_possible_duplicates()
    assert any(group.normalized_fio == "иванов иван иванович" for group in groups)

    result = merge_service.merge_players(primary_id, duplicate_id, "prefer_primary")

    assert result.results_transferred == 1
    assert players.get(duplicate_id) is None

    final_results = results.search(player_id=primary_id)
    assert len(final_results) == 2
    assert all(item["player_id"] == primary_id for item in final_results)

    updated_primary = players.get(primary_id)
    assert updated_primary is not None
    assert updated_primary["coach"] == "Coach 1"
    assert updated_primary["club"] == "Club 1"
    assert updated_primary["notes"] == "note"

    audit = connection.execute(
        "SELECT event_type, context_json FROM audit_log WHERE event_type = ? ORDER BY id DESC LIMIT 1",
        (MERGE_PLAYERS,),
    ).fetchone()
    assert audit is not None
    assert audit["event_type"] == MERGE_PLAYERS


def test_merge_players_rejects_same_player(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "app.db")
    players = PlayerRepository(connection)
    merge_service = PlayerMergeService(connection)

    player_id = players.create(
        {
            "last_name": "Петров",
            "first_name": "Пётр",
            "middle_name": None,
            "birth_date": None,
            "gender": "M",
            "coach": None,
            "club": None,
            "notes": None,
        }
    )

    try:
        merge_service.merge_players(player_id, player_id, "prefer_primary")
    except ValueError as exc:
        assert "самим собой" in str(exc)
    else:
        raise AssertionError("Expected ValueError for same player merge")

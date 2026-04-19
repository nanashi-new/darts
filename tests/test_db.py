import tempfile
import unittest
from pathlib import Path

import pytest

from app.db.database import get_connection
from app.db.repositories import PlayerRepository, ResultRepository, TournamentRepository


pytestmark = pytest.mark.integration


class DatabaseCrudTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.connection = get_connection(self.db_path)
        self.players = PlayerRepository(self.connection)
        self.tournaments = TournamentRepository(self.connection)
        self.results = ResultRepository(self.connection)

    def tearDown(self) -> None:
        self.connection.close()
        self.temp_dir.cleanup()

    def test_player_crud(self) -> None:
        player_id = self.players.create(
            {
                "last_name": "Ivanov",
                "first_name": "Ivan",
                "middle_name": "Ivanovich",
                "birth_date": "2000-01-01",
                "gender": "M",
                "coach": "Coach",
                "club": "Club",
                "notes": "Note",
            }
        )
        player = self.players.get(player_id)
        self.assertIsNotNone(player)
        self.assertEqual(player["last_name"], "Ivanov")

        self.players.update(
            player_id,
            {
                "last_name": "Petrov",
                "first_name": "Petr",
                "middle_name": None,
                "birth_date": "2001-01-01",
                "gender": "M",
                "coach": "Coach",
                "club": "Club",
                "notes": "Updated",
            },
        )
        updated = self.players.get(player_id)
        self.assertEqual(updated["last_name"], "Petrov")

        results = self.players.search("Pet")
        self.assertEqual(len(results), 1)

        self.players.delete(player_id)
        self.assertIsNone(self.players.get(player_id))

    def test_tournament_and_result_crud(self) -> None:
        player_id = self.players.create(
            {
                "last_name": "Sidorov",
                "first_name": "Sidor",
                "middle_name": None,
                "birth_date": "1999-12-31",
                "gender": "M",
                "coach": None,
                "club": None,
                "notes": None,
            }
        )
        tournament_id = self.tournaments.create(
            {
                "name": "Cup",
                "date": "2024-01-01",
                "category_code": "A",
                "league_code": "PREMIER",
                "is_adult_mode": 1,
                "source_files": "[]",
            }
        )
        tournament = self.tournaments.get(tournament_id)
        self.assertIsNotNone(tournament)
        self.assertEqual(tournament["is_adult_mode"], 1)

        result_id = self.results.create(
            {
                "tournament_id": tournament_id,
                "player_id": player_id,
                "place": 1,
                "score_set": 100,
                "score_sector20": 30,
                "score_big_round": 70,
                "rank_set": "A",
                "rank_sector20": "B",
                "rank_big_round": "C",
                "points_classification": 50,
                "points_place": 100,
                "points_total": 150,
                "calc_version": "v1",
            }
        )
        result = self.results.get(result_id)
        self.assertIsNotNone(result)
        self.assertEqual(result["points_total"], 150)

        self.results.update(
            result_id,
            {
                "tournament_id": tournament_id,
                "player_id": player_id,
                "place": 2,
                "score_set": 90,
                "score_sector20": 25,
                "score_big_round": 65,
                "rank_set": "B",
                "rank_sector20": "C",
                "rank_big_round": "D",
                "points_classification": 40,
                "points_place": 80,
                "points_total": 120,
                "calc_version": "v2",
            },
        )
        updated = self.results.get(result_id)
        self.assertEqual(updated["place"], 2)

        found = self.results.search(tournament_id=tournament_id)
        self.assertEqual(len(found), 1)

        self.results.delete(result_id)
        self.assertIsNone(self.results.get(result_id))

        self.tournaments.update(
            tournament_id,
            {
                "name": "Cup",
                "date": "2024-01-01",
                "category_code": "A",
                "league_code": "PREMIER",
                "is_adult_mode": 0,
                "source_files": "[]",
            },
        )
        updated_tournament = self.tournaments.get(tournament_id)
        self.assertEqual(updated_tournament["is_adult_mode"], 0)

        self.tournaments.delete(tournament_id)
        self.assertIsNone(self.tournaments.get(tournament_id))


if __name__ == "__main__":
    unittest.main()

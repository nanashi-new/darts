import pytest
import os
import tempfile
import unittest
from pathlib import Path

from app.db.database import get_connection
from app.db.repositories import PlayerRepository, ResultRepository, TournamentRepository
from app.services.recalculate_tournament import recalculate_tournament_results


pytestmark = pytest.mark.integration

class RecalculationTests(unittest.TestCase):
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

    def test_missing_norms_sets_classification_zero_and_warning(self) -> None:
        player_id = self.players.create(
            {
                "last_name": "Тест",
                "first_name": "Игрок",
                "middle_name": None,
                "birth_date": "2010-01-01",
                "gender": "M",
                "coach": None,
                "club": None,
                "notes": None,
            }
        )
        tournament_id = self.tournaments.create(
            {
                "name": "Турнир",
                "date": "2024-01-01",
                "category_code": "U15",
                "league_code": None,
                "source_files": "[]",
            }
        )
        result_id = self.results.create(
            {
                "tournament_id": tournament_id,
                "player_id": player_id,
                "place": 1,
                "score_set": 100,
                "score_sector20": 50,
                "score_big_round": 20,
                "rank_set": None,
                "rank_sector20": None,
                "rank_big_round": None,
                "points_classification": 999,
                "points_place": 0,
                "points_total": 999,
                "calc_version": "v1",
            }
        )

        previous = os.environ.get("NORMS_XLSX_PATH")
        broken_path = Path(self.temp_dir.name) / "broken.xlsx"
        broken_path.write_text("not-an-xlsx", encoding="utf-8")
        os.environ["NORMS_XLSX_PATH"] = str(broken_path)
        try:
            report = recalculate_tournament_results(
                connection=self.connection,
                tournament_id=tournament_id,
            )
        finally:
            if previous is None:
                os.environ.pop("NORMS_XLSX_PATH", None)
            else:
                os.environ["NORMS_XLSX_PATH"] = previous

        updated = self.results.get(result_id)
        self.assertEqual(updated["points_classification"], 0)
        self.assertGreaterEqual(len(report.warnings), 1)

    def test_recalculate_tournament_updates_points_total(self) -> None:
        player_id = self.players.create(
            {
                "last_name": "Иванов",
                "first_name": "Иван",
                "middle_name": None,
                "birth_date": "2012-01-01",
                "gender": "M",
                "coach": None,
                "club": None,
                "notes": None,
            }
        )
        tournament_id = self.tournaments.create(
            {
                "name": "Кубок",
                "date": "2024-01-01",
                "category_code": "U12",
                "league_code": None,
                "source_files": "[]",
            }
        )
        result_id = self.results.create(
            {
                "tournament_id": tournament_id,
                "player_id": player_id,
                "place": 2,
                "score_set": 0,
                "score_sector20": 0,
                "score_big_round": 0,
                "rank_set": "КМС",
                "rank_sector20": None,
                "rank_big_round": None,
                "points_classification": 200,
                "points_place": 1,
                "points_total": 201,
                "calc_version": "v1",
            }
        )

        report = recalculate_tournament_results(
            connection=self.connection,
            tournament_id=tournament_id,
        )

        updated = self.results.get(result_id)
        self.assertEqual(updated["points_place"], 12)
        self.assertEqual(updated["points_total"], updated["points_place"] + updated["points_classification"])
        self.assertEqual(report.results_updated, 1)

    def test_recalculate_adult_tournament_keeps_manual_totals(self) -> None:
        player_id = self.players.create(
            {
                "last_name": "Adultov",
                "first_name": "Alex",
                "middle_name": None,
                "birth_date": "1989-01-01",
                "gender": None,
                "coach": None,
                "club": None,
                "notes": None,
            }
        )
        tournament_id = self.tournaments.create(
            {
                "name": "Adult Cup",
                "date": "2026-04-20",
                "category_code": None,
                "league_code": None,
                "is_adult_mode": 1,
                "source_files": "[]",
            }
        )
        result_id = self.results.create(
            {
                "tournament_id": tournament_id,
                "player_id": player_id,
                "place": 1,
                "score_set": 999,
                "score_sector20": 999,
                "score_big_round": 999,
                "rank_set": "X",
                "rank_sector20": "Y",
                "rank_big_round": "Z",
                "points_classification": 50,
                "points_place": 70,
                "points_total": 120,
                "calc_version": "manual",
            }
        )

        report = recalculate_tournament_results(
            connection=self.connection,
            tournament_id=tournament_id,
        )

        updated = self.results.get(result_id)
        self.assertEqual(updated["points_classification"], 0)
        self.assertEqual(updated["points_place"], 120)
        self.assertEqual(updated["points_total"], 120)
        self.assertEqual(updated["calc_version"], "manual_adult_v1")
        self.assertEqual(report.results_updated, 1)


if __name__ == "__main__":
    unittest.main()

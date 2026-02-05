import unittest

from app.domain.ranks import calculate_points_classification


class ClassificationPointsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.norms = {
            "M": {
                "U10": {
                    "SET": [
                        (10, "3юн"),
                        (20, "2юн"),
                    ],
                    "SECTOR20": [(5, "3юн")],
                    "BIGROUND": [(1, "3юн")],
                },
                "U12": {
                    "SET": [(10, "3юн")],
                    "SECTOR20": [(5, "2юн")],
                    "BIGROUND": [(7, "1юн")],
                },
            }
        }

    def test_points_classification_u10_only_set(self) -> None:
        ranks, points = calculate_points_classification(
            score_set=15,
            score_sector20=99,
            score_big_round=99,
            gender="M",
            birth_date="2016-01-01",
            tournament_date="2025-01-01",
            norms=self.norms,
        )
        self.assertEqual(ranks["rank_set"], "3юн")
        self.assertIsNone(ranks["rank_sector20"])
        self.assertIsNone(ranks["rank_big_round"])
        self.assertEqual(points, 2)

    def test_points_classification_u12_all_disciplines(self) -> None:
        ranks, points = calculate_points_classification(
            score_set=12,
            score_sector20=5,
            score_big_round=7,
            gender="M",
            birth_date="2013-01-01",
            tournament_date="2024-06-01",
            norms=self.norms,
        )
        self.assertEqual(ranks["rank_set"], "3юн")
        self.assertEqual(ranks["rank_sector20"], "2юн")
        self.assertEqual(ranks["rank_big_round"], "1юн")
        self.assertEqual(points, 12)


if __name__ == "__main__":
    unittest.main()

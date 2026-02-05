import unittest

from app.domain.points import points_for_place, points_for_rank


class PointsForPlaceTests(unittest.TestCase):
    def test_points_for_place_table(self) -> None:
        cases = [
            (1, 14),
            (2, 12),
            (3, 10),
            (4, 10),
            (5, 8),
            (8, 8),
            (9, 6),
            (16, 6),
            (17, 4),
            (32, 4),
            (33, 2),
            (64, 2),
            (65, 0),
            (None, 0),
        ]
        for place, expected in cases:
            with self.subTest(place=place):
                self.assertEqual(points_for_place(place), expected)


class PointsForRankTests(unittest.TestCase):
    def test_points_for_rank_table(self) -> None:
        cases = [
            ("3юн", 2),
            ("2юн", 4),
            ("1юн", 6),
            ("3сп", 8),
            ("2сп", 10),
            ("1сп", 12),
            ("КМС", 14),
            (None, 0),
            ("", 0),
            ("неизвестный", 0),
        ]
        for rank, expected in cases:
            with self.subTest(rank=rank):
                self.assertEqual(points_for_rank(rank), expected)


if __name__ == "__main__":
    unittest.main()

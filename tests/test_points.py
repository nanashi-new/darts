import unittest

from app.domain.points import points_for_place


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


if __name__ == "__main__":
    unittest.main()

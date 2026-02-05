import unittest

from app.domain.rating import rolling_rating


class RollingRatingTests(unittest.TestCase):
    def test_rolling_rating_n3(self) -> None:
        points = [50, 40, 30, 20, 10]
        self.assertEqual(rolling_rating(points, 3), 120)

    def test_rolling_rating_n12(self) -> None:
        points = [15, 10, 8, 4]
        self.assertEqual(rolling_rating(points, 12), 37)


if __name__ == "__main__":
    unittest.main()

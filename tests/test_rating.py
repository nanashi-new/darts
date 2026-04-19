import unittest

import pytest

from app.domain.rating import (
    RatingBasisItem,
    RatingImpactRow,
    RatingSnapshotRow,
    build_rating_basis,
    build_rating_impact,
    build_rating_snapshot,
    normalize_adult_gender_scope,
    rolling_rating,
)


pytestmark = pytest.mark.unit


class RollingRatingTests(unittest.TestCase):
    def test_rolling_rating_n3(self) -> None:
        points = [50, 40, 30, 20, 10]
        self.assertEqual(rolling_rating(points, 3), 120)

    def test_rolling_rating_n12(self) -> None:
        points = [15, 10, 8, 4]
        self.assertEqual(rolling_rating(points, 12), 37)

    def test_build_rating_snapshot_uses_latest_n_results_per_player(self) -> None:
        results = [
            {
                "player_id": 1,
                "points_total": 50,
                "tournament_date": "2026-03-01",
                "last_name": "Adams",
                "first_name": "Alice",
                "middle_name": None,
            },
            {
                "player_id": 2,
                "points_total": 60,
                "tournament_date": "2026-02-28",
                "last_name": "Brown",
                "first_name": "Bob",
                "middle_name": None,
            },
            {
                "player_id": 1,
                "points_total": 40,
                "tournament_date": "2026-02-01",
                "last_name": "Adams",
                "first_name": "Alice",
                "middle_name": None,
            },
            {
                "player_id": 3,
                "points_total": 70,
                "tournament_date": "2026-01-20",
                "last_name": "Clark",
                "first_name": "Cara",
                "middle_name": None,
            },
            {
                "player_id": 1,
                "points_total": 30,
                "tournament_date": "2026-01-01",
                "last_name": "Adams",
                "first_name": "Alice",
                "middle_name": None,
            },
            {
                "player_id": 2,
                "points_total": 20,
                "tournament_date": "2025-12-01",
                "last_name": "Brown",
                "first_name": "Bob",
                "middle_name": None,
            },
        ]

        snapshot = build_rating_snapshot(results, 2)

        self.assertEqual(
            snapshot,
            [
                RatingSnapshotRow(
                    player_id=1,
                    place=1,
                    fio="Adams Alice",
                    points=90,
                    tournaments_count=2,
                ),
                RatingSnapshotRow(
                    player_id=2,
                    place=2,
                    fio="Brown Bob",
                    points=80,
                    tournaments_count=2,
                ),
                RatingSnapshotRow(
                    player_id=3,
                    place=3,
                    fio="Clark Cara",
                    points=70,
                    tournaments_count=1,
                ),
            ],
        )

    def test_build_rating_impact_handles_moved_new_and_unchanged_players(self) -> None:
        before = [
            RatingSnapshotRow(player_id=1, place=1, fio="Adams Alice", points=100, tournaments_count=2),
            RatingSnapshotRow(player_id=2, place=2, fio="Brown Bob", points=80, tournaments_count=2),
            RatingSnapshotRow(player_id=3, place=3, fio="Fox Frank", points=40, tournaments_count=1),
        ]
        after = [
            RatingSnapshotRow(player_id=2, place=1, fio="Brown Bob", points=120, tournaments_count=3),
            RatingSnapshotRow(player_id=1, place=2, fio="Adams Alice", points=100, tournaments_count=2),
            RatingSnapshotRow(player_id=3, place=3, fio="Fox Frank", points=40, tournaments_count=1),
            RatingSnapshotRow(player_id=4, place=4, fio="Dunn Dana", points=30, tournaments_count=1),
        ]

        impact = build_rating_impact(before, after)

        self.assertEqual(
            impact,
            [
                RatingImpactRow(
                    player_id=2,
                    fio="Brown Bob",
                    old_place=2,
                    new_place=1,
                    place_delta=1,
                    old_points=80,
                    new_points=120,
                    points_delta=40,
                ),
                RatingImpactRow(
                    player_id=1,
                    fio="Adams Alice",
                    old_place=1,
                    new_place=2,
                    place_delta=-1,
                    old_points=100,
                    new_points=100,
                    points_delta=0,
                ),
                RatingImpactRow(
                    player_id=4,
                    fio="Dunn Dana",
                    old_place=None,
                    new_place=4,
                    place_delta=None,
                    old_points=0,
                    new_points=30,
                    points_delta=30,
                ),
            ],
        )

    def test_build_rating_basis_uses_latest_n_results_deterministically(self) -> None:
        results = [
            {
                "player_id": 1,
                "tournament_id": 13,
                "tournament_date": "2026-03-01",
                "points_total": 30,
                "last_name": "Adams",
                "first_name": "Alice",
                "middle_name": None,
            },
            {
                "player_id": 1,
                "tournament_id": 15,
                "tournament_date": "2026-03-02",
                "points_total": 55,
                "last_name": "Adams",
                "first_name": "Alice",
                "middle_name": None,
            },
            {
                "player_id": 1,
                "tournament_id": 14,
                "tournament_date": "2026-03-02",
                "points_total": 40,
                "last_name": "Adams",
                "first_name": "Alice",
                "middle_name": None,
            },
            {
                "player_id": 2,
                "tournament_id": 12,
                "tournament_date": "2026-03-01",
                "points_total": 25,
                "last_name": "Brown",
                "first_name": "Bob",
                "middle_name": None,
            },
        ]

        basis = build_rating_basis(results, 2)

        self.assertEqual(
            basis[1],
            [
                RatingBasisItem(tournament_id=15, tournament_date="2026-03-02", points_total=55),
                RatingBasisItem(tournament_id=14, tournament_date="2026-03-02", points_total=40),
            ],
        )
        self.assertEqual(
            basis[2],
            [
                RatingBasisItem(tournament_id=12, tournament_date="2026-03-01", points_total=25),
            ],
        )

    def test_normalize_adult_gender_scope_uses_existing_gender_rules(self) -> None:
        self.assertEqual(normalize_adult_gender_scope("male"), "men")
        self.assertEqual(normalize_adult_gender_scope("мужской"), "men")
        self.assertEqual(normalize_adult_gender_scope("female"), "women")
        self.assertEqual(normalize_adult_gender_scope("женский"), "women")
        self.assertIsNone(normalize_adult_gender_scope(None))
        self.assertIsNone(normalize_adult_gender_scope("unknown"))


if __name__ == "__main__":
    unittest.main()

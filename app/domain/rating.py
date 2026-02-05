from __future__ import annotations


def compute_tournament_points(points_classification: int | None, points_place: int | None) -> int:
    """Compute total tournament points."""
    return int(points_classification or 0) + int(points_place or 0)


def rolling_rating(tournament_points_list_sorted_by_date_desc: list[int], n: int) -> int:
    """Sum the latest N tournament points from a list sorted by date desc."""
    if n <= 0:
        raise ValueError("N must be a positive integer.")
    return sum(tournament_points_list_sorted_by_date_desc[:n])

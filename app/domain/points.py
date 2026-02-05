from __future__ import annotations

from typing import Mapping


PLACE_POINTS: Mapping[range, int] = {
    range(1, 2): 14,
    range(2, 3): 12,
    range(3, 5): 10,
    range(5, 9): 8,
    range(9, 17): 6,
    range(17, 33): 4,
    range(33, 65): 2,
}

RANK_POINTS: Mapping[str, int] = {
    "3юн": 2,
    "2юн": 4,
    "1юн": 6,
    "3сп": 8,
    "2сп": 10,
    "1сп": 12,
    "КМС": 14,
    "3 юношеский": 2,
    "2 юношеский": 4,
    "1 юношеский": 6,
    "3 спортивный": 8,
    "2 спортивный": 10,
    "1 спортивный": 12,
}


def points_for_place(place: int | None) -> int:
    """Return rating points for a tournament place."""
    if place is None:
        return 0
    if not isinstance(place, int):
        raise TypeError("Place must be an integer or None.")
    if place <= 0:
        raise ValueError("Place must be a positive integer.")
    if place > 64:
        return 0
    for place_range, points in PLACE_POINTS.items():
        if place in place_range:
            return points
    return 0


def points_for_rank(rank: str | None) -> int:
    """Return rating points for a rank."""
    if not rank:
        return 0
    return RANK_POINTS.get(rank, 0)

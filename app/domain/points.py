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

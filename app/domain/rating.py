from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


def compute_tournament_points(points_classification: int | None, points_place: int | None) -> int:
    """Compute total tournament points."""
    return int(points_classification or 0) + int(points_place or 0)


def rolling_rating(tournament_points_list_sorted_by_date_desc: list[int], n: int) -> int:
    """Sum the latest N tournament points from a list sorted by date desc."""
    if n <= 0:
        raise ValueError("N must be a positive integer.")
    return sum(tournament_points_list_sorted_by_date_desc[:n])


@dataclass(frozen=True)
class RatingSnapshotRow:
    player_id: int
    place: int
    fio: str
    points: int
    tournaments_count: int


@dataclass(frozen=True)
class RatingBasisItem:
    tournament_id: int
    tournament_date: str
    points_total: int


@dataclass(frozen=True)
class RatingImpactRow:
    player_id: int
    fio: str
    old_place: int | None
    new_place: int | None
    place_delta: int | None
    old_points: int
    new_points: int
    points_delta: int


def _build_fio(entry: Mapping[str, Any]) -> str:
    last_name = str(entry.get("last_name") or "").strip()
    first_name = str(entry.get("first_name") or "").strip()
    middle_name = str(entry.get("middle_name") or "").strip()
    return " ".join(part for part in (last_name, first_name, middle_name) if part)


def _rating_entry_sort_key(entry: Mapping[str, Any]) -> tuple[str, int]:
    tournament_date = str(entry.get("tournament_date") or "")
    tournament_id = int(entry.get("tournament_id") or 0)
    return (tournament_date, tournament_id)


def _group_rating_entries(results: list[Mapping[str, Any]]) -> dict[int, dict[str, Any]]:
    players: dict[int, dict[str, Any]] = {}
    for entry in results:
        player_id = int(entry["player_id"])
        player_bucket = players.setdefault(player_id, {"entries": [], "fio": ""})
        player_bucket["entries"].append(entry)
        player_bucket["fio"] = _build_fio(entry)
    return players


def build_rating_snapshot(
    results: list[Mapping[str, Any]],
    n: int,
) -> list[RatingSnapshotRow]:
    if n <= 0:
        raise ValueError("N must be a positive integer.")

    players = _group_rating_entries(results)
    snapshot: list[RatingSnapshotRow] = []
    for player_id, player_bucket in players.items():
        entries = sorted(
            player_bucket["entries"],
            key=_rating_entry_sort_key,
            reverse=True,
        )
        points_list = [int(entry.get("points_total") or 0) for entry in entries]
        snapshot.append(
            RatingSnapshotRow(
                player_id=player_id,
                place=0,
                fio=str(player_bucket["fio"]),
                points=rolling_rating(points_list, n),
                tournaments_count=min(len(points_list), n),
            )
        )

    snapshot.sort(key=lambda row: (-row.points, row.fio))
    return [
        RatingSnapshotRow(
            player_id=row.player_id,
            place=index,
            fio=row.fio,
            points=row.points,
            tournaments_count=row.tournaments_count,
        )
        for index, row in enumerate(snapshot, start=1)
    ]


def build_rating_basis(
    results: list[Mapping[str, Any]],
    n: int,
) -> dict[int, list[RatingBasisItem]]:
    if n <= 0:
        raise ValueError("N must be a positive integer.")

    players = _group_rating_entries(results)
    basis: dict[int, list[RatingBasisItem]] = {}
    for player_id, player_bucket in players.items():
        entries = sorted(
            player_bucket["entries"],
            key=_rating_entry_sort_key,
            reverse=True,
        )
        basis[player_id] = [
            RatingBasisItem(
                tournament_id=int(entry.get("tournament_id") or 0),
                tournament_date=str(entry.get("tournament_date") or ""),
                points_total=int(entry.get("points_total") or 0),
            )
            for entry in entries[:n]
        ]
    return basis


def build_rating_impact(
    before_rows: list[RatingSnapshotRow],
    after_rows: list[RatingSnapshotRow],
) -> list[RatingImpactRow]:
    before_by_player = {row.player_id: row for row in before_rows}
    after_by_player = {row.player_id: row for row in after_rows}
    all_player_ids = sorted(set(before_by_player) | set(after_by_player))

    impact_rows: list[RatingImpactRow] = []
    for player_id in all_player_ids:
        before_row = before_by_player.get(player_id)
        after_row = after_by_player.get(player_id)
        if before_row is None and after_row is None:
            continue

        old_place = before_row.place if before_row is not None else None
        new_place = after_row.place if after_row is not None else None
        old_points = before_row.points if before_row is not None else 0
        new_points = after_row.points if after_row is not None else 0
        if old_place == new_place and old_points == new_points:
            continue

        place_delta: int | None = None
        if old_place is not None and new_place is not None:
            place_delta = old_place - new_place

        impact_rows.append(
            RatingImpactRow(
                player_id=player_id,
                fio=(after_row or before_row).fio,
                old_place=old_place,
                new_place=new_place,
                place_delta=place_delta,
                old_points=old_points,
                new_points=new_points,
                points_delta=new_points - old_points,
            )
        )

    impact_rows.sort(key=lambda row: (row.new_place is None, row.new_place or 10**9, row.fio))
    return impact_rows

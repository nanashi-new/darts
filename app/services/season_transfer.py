"""Season-level league transitions: relegate bottom of Premier, promote top of First."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from app.db.repositories import (
    LeagueTransferRepository,
    ResultRepository,
    TournamentRepository,
)
from app.domain.rating import build_rating_snapshot
from app.services.audit_log import AuditLogService, SEASON_TRANSFER_APPLIED
from app.services.restore_points import create_restore_point


@dataclass(frozen=True)
class SeasonTransferCandidate:
    player_id: int
    fio: str
    league_code: str
    rating_points: int
    rating_position: int


@dataclass(frozen=True)
class SeasonTransferPreview:
    available: bool
    reason: str | None
    relegated: list[SeasonTransferCandidate]
    promoted: list[SeasonTransferCandidate]
    warnings: list[str]


@dataclass(frozen=True)
class SeasonTransferResult:
    applied_count: int
    operation_group_id: str


def compute_season_transfer_candidates(
    *,
    connection,
    premier_league_code: str = "PREMIER",
    first_league_code: str = "FIRST",
    n: int = 3,
    transfer_count: int = 4,
) -> SeasonTransferPreview:
    """Compute candidates for season-level transfers between two leagues."""
    result_repo = ResultRepository(connection)

    premier_results = result_repo.list_results_for_rating(
        league_code=premier_league_code, statuses=["published"]
    )
    first_results = result_repo.list_results_for_rating(
        league_code=first_league_code, statuses=["published"]
    )

    if not premier_results or not first_results:
        return SeasonTransferPreview(
            available=False,
            reason="Нет опубликованных результатов для одной из лиг.",
            relegated=[],
            promoted=[],
            warnings=[],
        )

    premier_snapshot = build_rating_snapshot(premier_results, n)
    first_snapshot = build_rating_snapshot(first_results, n)

    warnings: list[str] = []

    relegated = _select_bottom(
        snapshot=premier_snapshot,
        league_code=premier_league_code,
        transfer_count=transfer_count,
        warnings=warnings,
    )

    promoted = _select_top(
        snapshot=first_snapshot,
        league_code=first_league_code,
        transfer_count=transfer_count,
        warnings=warnings,
    )

    return SeasonTransferPreview(
        available=True,
        reason=None,
        relegated=relegated,
        promoted=promoted,
        warnings=warnings,
    )


def apply_season_transfers(
    *,
    connection,
    preview: SeasonTransferPreview,
    actor: str = "season_transfer",
) -> SeasonTransferResult:
    """Apply computed season transfers: create marker tournament, record events, audit."""
    operation_group_id = str(uuid.uuid4())

    create_restore_point(
        connection=connection,
        title="Перед сезонными переходами",
        reason="season_transfer",
        source="season_transfer",
        operation_group_id=operation_group_id,
    )

    # Create a marker tournament to satisfy the FK constraint
    tournament_repo = TournamentRepository(connection)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    marker_tournament_id = tournament_repo.create(
        {
            "name": f"Сезонные переходы {now_str}",
            "date": now_str,
            "category_code": None,
            "league_code": None,
            "is_adult_mode": 0,
            "source_files": "[]",
            "status": "published",
            "type": "season_transfer",
        }
    )

    created_at = datetime.now(timezone.utc).isoformat(timespec="microseconds")
    entries: list[dict[str, object]] = []

    for candidate in preview.relegated:
        entries.append(
            {
                "player_id": candidate.player_id,
                "from_league_code": candidate.league_code,
                "to_league_code": "FIRST",
                "source_tournament_id": marker_tournament_id,
                "reason": "season_transfer",
                "operation_group_id": operation_group_id,
                "created_at": created_at,
            }
        )

    for candidate in preview.promoted:
        entries.append(
            {
                "player_id": candidate.player_id,
                "from_league_code": candidate.league_code,
                "to_league_code": "PREMIER",
                "source_tournament_id": marker_tournament_id,
                "reason": "season_transfer",
                "operation_group_id": operation_group_id,
                "created_at": created_at,
            }
        )

    transfer_repo = LeagueTransferRepository(connection)
    transfer_repo.create_many(entries)

    audit = AuditLogService(connection)
    for candidate in preview.relegated:
        audit.log_event(
            SEASON_TRANSFER_APPLIED,
            "Сезонный переход: вылет",
            f"{candidate.fio}: {candidate.league_code} -> FIRST",
            context={
                "player_id": candidate.player_id,
                "from_league_code": candidate.league_code,
                "to_league_code": "FIRST",
                "rating_points": candidate.rating_points,
                "rating_position": candidate.rating_position,
            },
            entity_type="player",
            entity_id=str(candidate.player_id),
            source=actor,
            operation_group_id=operation_group_id,
        )

    for candidate in preview.promoted:
        audit.log_event(
            SEASON_TRANSFER_APPLIED,
            "Сезонный переход: повышение",
            f"{candidate.fio}: {candidate.league_code} -> PREMIER",
            context={
                "player_id": candidate.player_id,
                "from_league_code": candidate.league_code,
                "to_league_code": "PREMIER",
                "rating_points": candidate.rating_points,
                "rating_position": candidate.rating_position,
            },
            entity_type="player",
            entity_id=str(candidate.player_id),
            source=actor,
            operation_group_id=operation_group_id,
        )

    return SeasonTransferResult(
        applied_count=len(entries),
        operation_group_id=operation_group_id,
    )


def _select_bottom(
    *,
    snapshot: list,
    league_code: str,
    transfer_count: int,
    warnings: list[str],
) -> list[SeasonTransferCandidate]:
    """Select the bottom transfer_count players from a rating snapshot (highest place = worst)."""
    total = len(snapshot)
    if total == 0:
        return []

    if total <= transfer_count:
        warnings.append(
            f"В лиге {league_code} менее {transfer_count} игроков, все будут переведены."
        )
        return [
            SeasonTransferCandidate(
                player_id=row.player_id,
                fio=row.fio,
                league_code=league_code,
                rating_points=row.points,
                rating_position=row.place,
            )
            for row in snapshot
        ]

    # Snapshot is sorted by points desc (place 1 = best). Bottom players are at the end.
    # Take from the end: positions (total - transfer_count + 1) .. total
    cutoff_index = total - transfer_count  # first index to include
    boundary_points = snapshot[cutoff_index].points

    # Check for ties at the boundary: include players above cutoff with same points
    start_index = cutoff_index
    while start_index > 0 and snapshot[start_index - 1].points == boundary_points:
        start_index -= 1

    selected = snapshot[start_index:]

    if len(selected) > transfer_count:
        tied_fios = [
            row.fio for row in selected if row.points == boundary_points
        ]
        warnings.append(
            f"Равенство очков на границе перехода ({league_code}): "
            + ", ".join(tied_fios)
        )

    return [
        SeasonTransferCandidate(
            player_id=row.player_id,
            fio=row.fio,
            league_code=league_code,
            rating_points=row.points,
            rating_position=row.place,
        )
        for row in selected
    ]


def _select_top(
    *,
    snapshot: list,
    league_code: str,
    transfer_count: int,
    warnings: list[str],
) -> list[SeasonTransferCandidate]:
    """Select the top transfer_count players from a rating snapshot (lowest place = best)."""
    total = len(snapshot)
    if total == 0:
        return []

    if total <= transfer_count:
        warnings.append(
            f"В лиге {league_code} менее {transfer_count} игроков, все будут переведены."
        )
        return [
            SeasonTransferCandidate(
                player_id=row.player_id,
                fio=row.fio,
                league_code=league_code,
                rating_points=row.points,
                rating_position=row.place,
            )
            for row in snapshot
        ]

    # Snapshot is sorted by points desc. Top players are at the start.
    boundary_points = snapshot[transfer_count - 1].points

    # Check for ties at the boundary: include players below cutoff with same points
    end_index = transfer_count
    while end_index < total and snapshot[end_index].points == boundary_points:
        end_index += 1

    selected = snapshot[:end_index]

    if len(selected) > transfer_count:
        tied_fios = [
            row.fio for row in selected if row.points == boundary_points
        ]
        warnings.append(
            f"Равенство очков на границе перехода ({league_code}): "
            + ", ".join(tied_fios)
        )

    return [
        SeasonTransferCandidate(
            player_id=row.player_id,
            fio=row.fio,
            league_code=league_code,
            rating_points=row.points,
            rating_position=row.place,
        )
        for row in selected
    ]

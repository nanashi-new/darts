from __future__ import annotations

from dataclasses import dataclass
from sqlite3 import Connection

from app.db.repositories import (
    TOURNAMENT_STATUS_PUBLISHED,
    ResultRepository,
    TournamentRepository,
)
from app.domain.rating import (
    RatingImpactRow,
    RatingSnapshotRow,
    build_rating_impact,
    build_rating_snapshot,
)


@dataclass(frozen=True)
class ImportRatingImpactPreview:
    available: bool
    reason: str | None
    before_rows: list[RatingSnapshotRow]
    after_rows: list[RatingSnapshotRow]
    rows: list[RatingImpactRow]


def _preview_unavailable(reason: str) -> ImportRatingImpactPreview:
    return ImportRatingImpactPreview(
        available=False,
        reason=reason,
        before_rows=[],
        after_rows=[],
        rows=[],
    )


def build_import_rating_preview(
    *,
    connection: Connection,
    tournament_id: int,
    n_value: int = 6,
) -> ImportRatingImpactPreview:
    tournament_repo = TournamentRepository(connection)
    result_repo = ResultRepository(connection)

    tournament = tournament_repo.get(tournament_id)
    if tournament is None:
        return _preview_unavailable("Tournament was not found.")

    category_code = str(tournament.get("category_code") or "").strip()
    if not category_code:
        return _preview_unavailable("Rating impact preview is unavailable because category code is missing.")

    current_rows = result_repo.list_with_players(tournament_id)
    if not current_rows:
        return _preview_unavailable("Rating impact preview is unavailable because tournament has no results yet.")

    baseline_rows = [
        row
        for row in result_repo.list_results_for_rating(
            category_code=category_code,
            statuses=[TOURNAMENT_STATUS_PUBLISHED],
        )
        if int(row.get("tournament_id") or 0) != tournament_id
    ]

    candidate_rows = list(baseline_rows)
    tournament_date = tournament.get("date")
    for row in current_rows:
        candidate_rows.append(
            {
                "player_id": row["player_id"],
                "tournament_id": tournament_id,
                "points_total": row["points_total"],
                "tournament_date": tournament_date,
                "last_name": row["last_name"],
                "first_name": row["first_name"],
                "middle_name": row["middle_name"],
            }
        )

    before_snapshot = build_rating_snapshot(baseline_rows, n_value)
    after_snapshot = build_rating_snapshot(candidate_rows, n_value)
    impact_rows = build_rating_impact(before_snapshot, after_snapshot)

    return ImportRatingImpactPreview(
        available=True,
        reason=None,
        before_rows=before_snapshot,
        after_rows=after_snapshot,
        rows=impact_rows,
    )

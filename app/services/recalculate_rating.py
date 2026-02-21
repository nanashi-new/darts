from __future__ import annotations

from app.services.recalculate_tournament import (
    RecalculationReport,
    recalculate_all_tournaments,
    recalculate_tournament_results,
)


class RecalculateRatingService:
    """Compatibility wrapper for rating recalculation flows."""

    def run(
        self,
        *,
        connection,
        tournament_id: int | None = None,
    ) -> RecalculationReport:
        if connection is None:
            raise ValueError("connection is required")

        if tournament_id is None:
            return recalculate_all_tournaments(connection=connection)

        if not isinstance(tournament_id, int) or tournament_id <= 0:
            raise ValueError("tournament_id must be a positive integer")

        return recalculate_tournament_results(connection=connection, tournament_id=tournament_id)

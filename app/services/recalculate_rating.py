from __future__ import annotations

from app.services.recalculate_tournament import (
    RecalculationReport,
    recalculate_all_tournaments,
    recalculate_tournament_results,
)


class RecalculateRatingService:
    """Backwards-compatible façade for tournament rating recalculation."""

    def run(self, *, connection, tournament_id: int | None = None) -> RecalculationReport:
        """Recalculate ratings for one tournament or for all tournaments.

        Args:
            connection: Open DB connection.
            tournament_id: Tournament ID for a targeted recalculation.
                If omitted, recalculation is performed for all tournaments.

        Raises:
            ValueError: If ``connection`` is missing or ``tournament_id`` is invalid.
        """
        if connection is None:
            raise ValueError("connection is required")

        if tournament_id is None:
            return recalculate_all_tournaments(connection=connection)

        if not isinstance(tournament_id, int) or tournament_id <= 0:
            raise ValueError("tournament_id must be a positive integer")

        return recalculate_tournament_results(
            connection=connection,
            tournament_id=tournament_id,
        )

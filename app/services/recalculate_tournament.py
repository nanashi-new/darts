from __future__ import annotations

from app.db.repositories import ResultRepository, TournamentRepository
from app.domain.points import points_for_place
from app.domain.ranks import calculate_points_classification
from app.services.norms_loader import load_norms_from_settings


def recalculate_tournament_results(*, connection, tournament_id: int) -> bool:
    tournament_repo = TournamentRepository(connection)
    result_repo = ResultRepository(connection)

    tournament = tournament_repo.get(tournament_id)
    if not tournament:
        raise ValueError("Турнир не найден.")

    norms, norms_loaded = load_norms_from_settings()

    results = result_repo.list_with_players(tournament_id)
    for result in results:
        place = result.get("place")
        points_place = points_for_place(place) if place is not None else 0

        ranks, points_classification = calculate_points_classification(
            score_set=result.get("score_set"),
            score_sector20=result.get("score_sector20"),
            score_big_round=result.get("score_big_round"),
            gender=result.get("gender"),
            birth_date=result.get("birth_date"),
            tournament_date=tournament.get("date"),
            norms=norms or {},
        )

        points_total = points_place + points_classification

        result_repo.update(
            int(result["id"]),
            {
                "tournament_id": result.get("tournament_id"),
                "player_id": result.get("player_id"),
                "place": place,
                "score_set": result.get("score_set"),
                "score_sector20": result.get("score_sector20"),
                "score_big_round": result.get("score_big_round"),
                "rank_set": ranks["rank_set"],
                "rank_sector20": ranks["rank_sector20"],
                "rank_big_round": ranks["rank_big_round"],
                "points_classification": points_classification,
                "points_place": points_place,
                "points_total": points_total,
                "calc_version": "v2",
            },
        )

    return norms_loaded

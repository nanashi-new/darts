from __future__ import annotations

from dataclasses import dataclass, field

from app.db.repositories import ResultRepository, TournamentRepository
from app.domain.points import points_for_place
from app.domain.ranks import calculate_points_classification
from app.services.norms_loader import load_norms_from_settings


@dataclass
class RecalculationReport:
    tournaments_processed: int = 0
    results_updated: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def recalculate_tournament_results(*, connection, tournament_id: int) -> RecalculationReport:
    tournament_repo = TournamentRepository(connection)
    result_repo = ResultRepository(connection)
    report = RecalculationReport()

    tournament = tournament_repo.get(tournament_id)
    if not tournament:
        raise ValueError("Турнир не найден.")

    norms_load = load_norms_from_settings()
    norms, norms_loaded = norms_load.norms, norms_load.loaded
    if not norms_loaded:
        report.warnings.append(norms_load.warning or "Нормативы не загружены.")

    results = result_repo.list_with_players(tournament_id)
    report.tournaments_processed = 1
    for result in results:
        try:
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
            report.results_updated += 1
        except Exception as exc:  # noqa: BLE001
            report.errors.append(f"result_id={result.get('id')}: {exc}")

    return report


def recalculate_all_tournaments(*, connection) -> RecalculationReport:
    tournament_repo = TournamentRepository(connection)
    report = RecalculationReport()
    for tournament in tournament_repo.list():
        tournament_id = int(tournament["id"])
        try:
            one_report = recalculate_tournament_results(
                connection=connection,
                tournament_id=tournament_id,
            )
            report.tournaments_processed += one_report.tournaments_processed
            report.results_updated += one_report.results_updated
            report.warnings.extend(
                f"tournament_id={tournament_id}: {item}" for item in one_report.warnings
            )
            report.errors.extend(
                f"tournament_id={tournament_id}: {item}" for item in one_report.errors
            )
        except Exception as exc:  # noqa: BLE001
            report.errors.append(f"tournament_id={tournament_id}: {exc}")
    return report

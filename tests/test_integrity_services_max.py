from __future__ import annotations

from pathlib import Path

from app.db.database import get_connection
from app.db.repositories import PlayerRepository, ResultRepository, TournamentRepository
from app.services.audit_log import (
    AuditLogService,
    EXPORT_BATCH,
    MERGE_PLAYERS,
    RECALC_ALL,
    RECALC_TOURNAMENT,
)
from app.services.batch_export import BatchExportService
from app.services.player_merge import PlayerMergeService
from app.services.recalculate_tournament import recalculate_all_tournaments, recalculate_tournament_results


def test_integrity_services_max(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "integrity.db")
    players = PlayerRepository(connection)
    tournaments = TournamentRepository(connection)
    results = ResultRepository(connection)
    merge_service = PlayerMergeService(connection)
    audit = AuditLogService(connection)

    p1 = players.create({"last_name": "Иванов", "first_name": "Иван", "middle_name": None, "birth_date": "2010-01-01", "gender": "M", "coach": None, "club": None, "notes": None})
    p2 = players.create({"last_name": "Иванов", "first_name": "Иван", "middle_name": None, "birth_date": "2010-01-01", "gender": "M", "coach": "Coach", "club": None, "notes": None})
    p3 = players.create({"last_name": "Петров", "first_name": "Пётр", "middle_name": None, "birth_date": "2011-01-01", "gender": "M", "coach": None, "club": None, "notes": None})

    t1 = tournaments.create({"name": "Cup 1", "date": "2025-01-01", "category_code": "U12", "league_code": None, "source_files": "[]"})
    t2 = tournaments.create({"name": "Cup 2", "date": "2025-01-02", "category_code": "U12", "league_code": None, "source_files": "[]"})

    results.create({"tournament_id": t1, "player_id": p1, "place": 1, "score_set": 100, "score_sector20": 20, "score_big_round": 40, "rank_set": None, "rank_sector20": None, "rank_big_round": None, "points_classification": 0, "points_place": 0, "points_total": 0, "calc_version": "v1"})
    results.create({"tournament_id": t1, "player_id": p2, "place": 2, "score_set": 90, "score_sector20": 15, "score_big_round": 35, "rank_set": None, "rank_sector20": None, "rank_big_round": None, "points_classification": 0, "points_place": 0, "points_total": 0, "calc_version": "v1"})
    results.create({"tournament_id": t2, "player_id": p2, "place": 1, "score_set": 95, "score_sector20": 18, "score_big_round": 38, "rank_set": None, "rank_sector20": None, "rank_big_round": None, "points_classification": 0, "points_place": 0, "points_total": 0, "calc_version": "v1"})
    results.create({"tournament_id": t2, "player_id": p3, "place": 2, "score_set": 80, "score_sector20": 12, "score_big_round": 30, "rank_set": None, "rank_sector20": None, "rank_big_round": None, "points_classification": 0, "points_place": 0, "points_total": 0, "calc_version": "v1"})

    recalc_one = recalculate_tournament_results(connection=connection, tournament_id=t1)
    audit.log_event(RECALC_TOURNAMENT, "Пересчёт турнира", f"updated={recalc_one.results_updated}")

    recalc_all = recalculate_all_tournaments(connection=connection)
    audit.log_event(RECALC_ALL, "Пересчёт всего", f"updated={recalc_all.results_updated}")

    batch = BatchExportService(connection).export_all(tmp_path, export_format="xlsx", n_value=6)
    audit.log_event(EXPORT_BATCH, "Batch export", f"files={len(batch.files_created)}")

    merge_result = merge_service.merge_players(primary_id=p1, duplicate_id=p2, merge_strategy="prefer_primary")
    assert merge_result.results_transferred >= 1
    assert merge_result.duplicate_results_removed >= 1

    orphan_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM results r
        LEFT JOIN players p ON p.id = r.player_id
        LEFT JOIN tournaments t ON t.id = r.tournament_id
        WHERE p.id IS NULL OR t.id IS NULL
        """
    ).fetchone()[0]
    assert orphan_count == 0

    unique_conflicts = connection.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT tournament_id, player_id, COUNT(*) AS c
            FROM results
            GROUP BY tournament_id, player_id
            HAVING c > 1
        )
        """
    ).fetchone()[0]
    assert unique_conflicts == 0

    events = {item.event_type for item in audit.list_events()}
    assert {RECALC_TOURNAMENT, RECALC_ALL, EXPORT_BATCH, MERGE_PLAYERS}.issubset(events)

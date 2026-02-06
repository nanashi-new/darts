from __future__ import annotations

import time
from pathlib import Path

from app.db.database import get_connection
from app.db.repositories import PlayerRepository, ResultRepository, TournamentRepository
from app.services.batch_export import BatchExportService


def _seed_for_export(connection) -> None:
    players = PlayerRepository(connection)
    tournaments = TournamentRepository(connection)
    results = ResultRepository(connection)

    player_ids: list[int] = []
    for i in range(100):
        player_ids.append(
            players.create(
                {
                    "last_name": f"P{i}",
                    "first_name": "N",
                    "middle_name": None,
                    "birth_date": "2010-01-01",
                    "gender": "M",
                    "coach": None,
                    "club": None,
                    "notes": None,
                }
            )
        )

    tournament_ids: list[int] = []
    for t in range(20):
        tournament_ids.append(
            tournaments.create(
                {
                    "name": f"T{t}",
                    "date": f"2025-02-{(t % 28) + 1:02d}",
                    "category_code": "U12",
                    "league_code": None,
                    "source_files": "[]",
                }
            )
        )

    for t_idx, tournament_id in enumerate(tournament_ids):
        for p_idx, player_id in enumerate(player_ids):
            results.create(
                {
                    "tournament_id": tournament_id,
                    "player_id": player_id,
                    "place": p_idx + 1,
                    "score_set": 100 - (p_idx % 40),
                    "score_sector20": p_idx % 20,
                    "score_big_round": p_idx % 10,
                    "rank_set": None,
                    "rank_sector20": None,
                    "rank_big_round": None,
                    "points_classification": t_idx % 5,
                    "points_place": max(0, 100 - p_idx),
                    "points_total": max(0, 100 - p_idx) + (t_idx % 5),
                    "calc_version": "v1",
                }
            )


def test_perf_export_batch_max(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "perf_export.db")
    _seed_for_export(connection)

    started = time.perf_counter()
    result = BatchExportService(connection).export_all(tmp_path, export_format="xlsx", n_value=6)
    duration = time.perf_counter() - started

    assert duration < 10.0
    assert result.files_created
    assert all(path.exists() and path.stat().st_size > 0 for path in result.files_created)

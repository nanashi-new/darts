"""Tests for the analytics service."""

from __future__ import annotations

import sqlite3
import statistics
from pathlib import Path

import pytest

from app.db.schema import initialize_schema
from app.services.analytics import AnalyticsService


@pytest.fixture()
def connection(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    initialize_schema(conn)
    return conn


def _create_player(
    conn: sqlite3.Connection,
    *,
    last_name: str,
    first_name: str,
    middle_name: str | None = None,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO players (last_name, first_name, middle_name)
        VALUES (?, ?, ?)
        """,
        (last_name, first_name, middle_name),
    )
    conn.commit()
    assert cursor.lastrowid is not None
    return int(cursor.lastrowid)


def _create_tournament(
    conn: sqlite3.Connection,
    *,
    name: str,
    date: str,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO tournaments (name, date, category_code, league_code, source_files)
        VALUES (?, ?, 'A', 'L1', '[]')
        """,
        (name, date),
    )
    conn.commit()
    assert cursor.lastrowid is not None
    return int(cursor.lastrowid)


def _create_result(
    conn: sqlite3.Connection,
    *,
    tournament_id: int,
    player_id: int,
    place: int,
    points_total: int,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO results (tournament_id, player_id, place, points_total)
        VALUES (?, ?, ?, ?)
        """,
        (tournament_id, player_id, place, points_total),
    )
    conn.commit()
    assert cursor.lastrowid is not None
    return int(cursor.lastrowid)


class TestTournamentStats:
    def test_basic_stats(self, connection: sqlite3.Connection) -> None:
        service = AnalyticsService()
        t_id = _create_tournament(connection, name="T1", date="2024-01-15")
        p1 = _create_player(connection, last_name="A", first_name="X")
        p2 = _create_player(connection, last_name="B", first_name="Y")
        p3 = _create_player(connection, last_name="C", first_name="Z")
        p4 = _create_player(connection, last_name="D", first_name="W")
        p5 = _create_player(connection, last_name="E", first_name="V")

        points = [100, 80, 60, 40, 20]
        for i, (pid, pts) in enumerate(
            zip([p1, p2, p3, p4, p5], points), start=1
        ):
            _create_result(
                connection, tournament_id=t_id, player_id=pid, place=i, points_total=pts
            )

        stats = service.tournament_stats(connection, t_id)
        assert stats is not None
        assert stats.participant_count == 5
        assert stats.avg_points == statistics.mean(points)
        assert stats.median_points == statistics.median(points)
        assert stats.min_points == 20
        assert stats.max_points == 100
        assert stats.place_distribution == {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}

    def test_empty_tournament(self, connection: sqlite3.Connection) -> None:
        service = AnalyticsService()
        t_id = _create_tournament(connection, name="Empty", date="2024-02-01")
        stats = service.tournament_stats(connection, t_id)
        assert stats is None


class TestPlayerProgress:
    def test_chronological_order(self, connection: sqlite3.Connection) -> None:
        service = AnalyticsService()
        p1 = _create_player(connection, last_name="Alpha", first_name="One")
        t1 = _create_tournament(connection, name="T-Jan", date="2024-01-10")
        t2 = _create_tournament(connection, name="T-Mar", date="2024-03-10")
        t3 = _create_tournament(connection, name="T-Feb", date="2024-02-10")

        _create_result(connection, tournament_id=t1, player_id=p1, place=3, points_total=50)
        _create_result(connection, tournament_id=t2, player_id=p1, place=1, points_total=100)
        _create_result(connection, tournament_id=t3, player_id=p1, place=2, points_total=75)

        progress = service.player_progress(connection, p1)
        assert len(progress) == 3
        # Should be ordered by date ascending
        assert progress[0].date == "2024-01-10"
        assert progress[1].date == "2024-02-10"
        assert progress[2].date == "2024-03-10"
        assert progress[0].points_total == 50
        assert progress[1].points_total == 75
        assert progress[2].points_total == 100


class TestComparePlayers:
    def test_two_players(self, connection: sqlite3.Connection) -> None:
        service = AnalyticsService()
        p1 = _create_player(connection, last_name="Ivanov", first_name="Ivan")
        p2 = _create_player(connection, last_name="Petrov", first_name="Petr")

        t1 = _create_tournament(connection, name="T1", date="2024-01-01")
        t2 = _create_tournament(connection, name="T2", date="2024-02-01")

        _create_result(connection, tournament_id=t1, player_id=p1, place=1, points_total=100)
        _create_result(connection, tournament_id=t2, player_id=p1, place=2, points_total=80)
        _create_result(connection, tournament_id=t1, player_id=p2, place=3, points_total=60)
        _create_result(connection, tournament_id=t2, player_id=p2, place=1, points_total=90)

        result = service.compare_players(connection, [p1, p2])
        assert len(result) == 2

        # Player 1
        assert result[0].player_id == p1
        assert result[0].tournaments_count == 2
        assert result[0].avg_points == statistics.mean([100, 80])
        assert result[0].best_position == 1
        assert result[0].worst_position == 2
        assert result[0].win_count == 1

        # Player 2
        assert result[1].player_id == p2
        assert result[1].tournaments_count == 2
        assert result[1].avg_points == statistics.mean([60, 90])
        assert result[1].best_position == 1
        assert result[1].worst_position == 3
        assert result[1].win_count == 1


class TestPlayerStability:
    def test_correct_stdev(self, connection: sqlite3.Connection) -> None:
        service = AnalyticsService()
        p1 = _create_player(connection, last_name="Sidorov", first_name="Sid")
        t1 = _create_tournament(connection, name="T1", date="2024-01-01")
        t2 = _create_tournament(connection, name="T2", date="2024-02-01")
        t3 = _create_tournament(connection, name="T3", date="2024-03-01")

        points = [100, 60, 80]
        _create_result(connection, tournament_id=t1, player_id=p1, place=1, points_total=points[0])
        _create_result(connection, tournament_id=t2, player_id=p1, place=2, points_total=points[1])
        _create_result(connection, tournament_id=t3, player_id=p1, place=1, points_total=points[2])

        stability = service.player_stability(connection, p1)
        expected = statistics.stdev(points)
        assert abs(stability - expected) < 0.001

    def test_single_result_returns_zero(self, connection: sqlite3.Connection) -> None:
        service = AnalyticsService()
        p1 = _create_player(connection, last_name="Solo", first_name="One")
        t1 = _create_tournament(connection, name="T1", date="2024-01-01")
        _create_result(connection, tournament_id=t1, player_id=p1, place=1, points_total=100)

        stability = service.player_stability(connection, p1)
        assert stability == 0.0


class TestTopResults:
    def test_with_period_filter(self, connection: sqlite3.Connection) -> None:
        service = AnalyticsService()
        p1 = _create_player(connection, last_name="Top", first_name="Player")
        t1 = _create_tournament(connection, name="T-Jan", date="2024-01-15")
        t2 = _create_tournament(connection, name="T-Mar", date="2024-03-15")
        t3 = _create_tournament(connection, name="T-Jun", date="2024-06-15")

        _create_result(connection, tournament_id=t1, player_id=p1, place=1, points_total=100)
        _create_result(connection, tournament_id=t2, player_id=p1, place=1, points_total=120)
        _create_result(connection, tournament_id=t3, player_id=p1, place=1, points_total=90)

        # Filter to Feb-Apr
        results = service.top_results(
            connection, period_start="2024-02-01", period_end="2024-04-30"
        )
        assert len(results) == 1
        assert results[0].points_total == 120
        assert results[0].tournament_name == "T-Mar"

    def test_limit(self, connection: sqlite3.Connection) -> None:
        service = AnalyticsService()
        t1 = _create_tournament(connection, name="T1", date="2024-01-01")
        for i in range(5):
            pid = _create_player(connection, last_name=f"P{i}", first_name="X")
            _create_result(
                connection, tournament_id=t1, player_id=pid, place=i + 1, points_total=100 - i * 10
            )

        results = service.top_results(connection, limit=3)
        assert len(results) == 3
        assert results[0].points_total == 100
        assert results[2].points_total == 80


class TestTournamentTrends:
    def test_grouping_by_month(self, connection: sqlite3.Connection) -> None:
        service = AnalyticsService()
        p1 = _create_player(connection, last_name="Trend", first_name="Player")

        # Two tournaments in January
        t1 = _create_tournament(connection, name="T1-Jan", date="2024-01-10")
        t2 = _create_tournament(connection, name="T2-Jan", date="2024-01-20")
        # One tournament in February
        t3 = _create_tournament(connection, name="T1-Feb", date="2024-02-15")

        p2 = _create_player(connection, last_name="Trend2", first_name="Player2")

        _create_result(connection, tournament_id=t1, player_id=p1, place=1, points_total=100)
        _create_result(connection, tournament_id=t2, player_id=p1, place=1, points_total=80)
        _create_result(connection, tournament_id=t2, player_id=p2, place=2, points_total=70)
        _create_result(connection, tournament_id=t3, player_id=p1, place=1, points_total=90)

        trends = service.tournament_trends(connection)
        assert len(trends) == 2
        assert trends[0].period == "2024-01"
        assert trends[0].tournament_count == 2
        assert trends[1].period == "2024-02"
        assert trends[1].tournament_count == 1

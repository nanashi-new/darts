"""Analytics service for tournaments and players."""

from __future__ import annotations

import sqlite3
import statistics
from dataclasses import dataclass


@dataclass(frozen=True)
class TournamentStats:
    avg_points: float
    median_points: float
    min_points: int
    max_points: int
    place_distribution: dict[int, int]
    participant_count: int


@dataclass(frozen=True)
class TournamentComparisonEntry:
    tournament_id: int
    name: str
    date: str
    avg_points: float
    participant_count: int
    top_score: int


@dataclass(frozen=True)
class PlayerProgressEntry:
    tournament_id: int
    tournament_name: str
    date: str
    place: int
    points_total: int


@dataclass(frozen=True)
class PlayerComparisonEntry:
    player_id: int
    fio: str
    tournaments_count: int
    avg_points: float
    avg_position: float
    best_position: int
    worst_position: int
    win_count: int
    stability: float


@dataclass(frozen=True)
class TopResultEntry:
    player_id: int
    fio: str
    tournament_name: str
    date: str
    points_total: int
    place: int


@dataclass(frozen=True)
class TournamentTrendEntry:
    period: str
    tournament_count: int
    avg_participants: float
    avg_level: float


class AnalyticsService:
    """Analytics computations over tournaments and players."""

    def tournament_stats(
        self, connection: sqlite3.Connection, tournament_id: int
    ) -> TournamentStats | None:
        rows = connection.execute(
            "SELECT points_total, place FROM results WHERE tournament_id = ?",
            (tournament_id,),
        ).fetchall()
        if not rows:
            return None
        points = [int(row[0]) for row in rows if row[0] is not None]
        if not points:
            return None
        places = [int(row[1]) for row in rows if row[1] is not None]
        place_distribution: dict[int, int] = {}
        for p in places:
            place_distribution[p] = place_distribution.get(p, 0) + 1
        return TournamentStats(
            avg_points=statistics.mean(points),
            median_points=statistics.median(points),
            min_points=min(points),
            max_points=max(points),
            place_distribution=place_distribution,
            participant_count=len(rows),
        )

    def compare_tournaments(
        self, connection: sqlite3.Connection, tournament_ids: list[int]
    ) -> list[TournamentComparisonEntry]:
        if not tournament_ids:
            return []
        placeholders = ", ".join("?" for _ in tournament_ids)
        rows = connection.execute(
            f"""
            SELECT
                t.id,
                t.name,
                t.date,
                AVG(r.points_total) AS avg_points,
                COUNT(r.id) AS participant_count,
                MAX(r.points_total) AS top_score
            FROM tournaments t
            JOIN results r ON r.tournament_id = t.id
            WHERE t.id IN ({placeholders})
            GROUP BY t.id, t.name, t.date
            ORDER BY t.date DESC
            """,
            tournament_ids,
        ).fetchall()
        return [
            TournamentComparisonEntry(
                tournament_id=int(row[0]),
                name=str(row[1] or ""),
                date=str(row[2] or ""),
                avg_points=float(row[3] or 0),
                participant_count=int(row[4]),
                top_score=int(row[5] or 0),
            )
            for row in rows
        ]

    def player_progress(
        self, connection: sqlite3.Connection, player_id: int
    ) -> list[PlayerProgressEntry]:
        rows = connection.execute(
            """
            SELECT
                r.tournament_id,
                t.name,
                t.date,
                r.place,
                r.points_total
            FROM results r
            JOIN tournaments t ON t.id = r.tournament_id
            WHERE r.player_id = ?
            ORDER BY t.date ASC, t.id ASC
            """,
            (player_id,),
        ).fetchall()
        return [
            PlayerProgressEntry(
                tournament_id=int(row[0]),
                tournament_name=str(row[1] or ""),
                date=str(row[2] or ""),
                place=int(row[3] or 0),
                points_total=int(row[4] or 0),
            )
            for row in rows
        ]

    def compare_players(
        self, connection: sqlite3.Connection, player_ids: list[int]
    ) -> list[PlayerComparisonEntry]:
        result: list[PlayerComparisonEntry] = []
        for player_id in player_ids:
            player_row = connection.execute(
                "SELECT last_name, first_name, middle_name FROM players WHERE id = ?",
                (player_id,),
            ).fetchone()
            if player_row is None:
                continue
            fio = " ".join(
                part
                for part in [player_row[0], player_row[1], player_row[2]]
                if part
            )
            rows = connection.execute(
                "SELECT place, points_total FROM results WHERE player_id = ?",
                (player_id,),
            ).fetchall()
            if not rows:
                result.append(
                    PlayerComparisonEntry(
                        player_id=player_id,
                        fio=fio,
                        tournaments_count=0,
                        avg_points=0.0,
                        avg_position=0.0,
                        best_position=0,
                        worst_position=0,
                        win_count=0,
                        stability=0.0,
                    )
                )
                continue
            points = [int(r[1]) for r in rows if r[1] is not None]
            places = [int(r[0]) for r in rows if r[0] is not None]
            avg_points = statistics.mean(points) if points else 0.0
            avg_position = statistics.mean(places) if places else 0.0
            best_position = min(places) if places else 0
            worst_position = max(places) if places else 0
            win_count = sum(1 for p in places if p == 1)
            stability = statistics.stdev(points) if len(points) >= 2 else 0.0
            result.append(
                PlayerComparisonEntry(
                    player_id=player_id,
                    fio=fio,
                    tournaments_count=len(rows),
                    avg_points=avg_points,
                    avg_position=avg_position,
                    best_position=best_position,
                    worst_position=worst_position,
                    win_count=win_count,
                    stability=stability,
                )
            )
        return result

    def player_stability(
        self, connection: sqlite3.Connection, player_id: int
    ) -> float:
        rows = connection.execute(
            "SELECT points_total FROM results WHERE player_id = ?",
            (player_id,),
        ).fetchall()
        points = [int(r[0]) for r in rows if r[0] is not None]
        if len(points) < 2:
            return 0.0
        return statistics.stdev(points)

    def top_results(
        self,
        connection: sqlite3.Connection,
        period_start: str | None = None,
        period_end: str | None = None,
        limit: int = 10,
    ) -> list[TopResultEntry]:
        clauses: list[str] = []
        params: list[object] = []
        if period_start:
            clauses.append("t.date >= ?")
            params.append(period_start)
        if period_end:
            clauses.append("t.date <= ?")
            params.append(period_end)
        where_sql = ""
        if clauses:
            where_sql = "WHERE " + " AND ".join(clauses)
        params.append(limit)
        rows = connection.execute(
            f"""
            SELECT
                r.player_id,
                p.last_name,
                p.first_name,
                p.middle_name,
                t.name,
                t.date,
                r.points_total,
                r.place
            FROM results r
            JOIN players p ON p.id = r.player_id
            JOIN tournaments t ON t.id = r.tournament_id
            {where_sql}
            ORDER BY r.points_total DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [
            TopResultEntry(
                player_id=int(row[0]),
                fio=" ".join(part for part in [row[1], row[2], row[3]] if part),
                tournament_name=str(row[4] or ""),
                date=str(row[5] or ""),
                points_total=int(row[6] or 0),
                place=int(row[7] or 0),
            )
            for row in rows
        ]

    def tournament_trends(
        self, connection: sqlite3.Connection
    ) -> list[TournamentTrendEntry]:
        rows = connection.execute(
            """
            SELECT
                SUBSTR(t.date, 1, 7) AS period,
                COUNT(DISTINCT t.id) AS tournament_count,
                COUNT(r.id) * 1.0 / MAX(COUNT(DISTINCT t.id), 1) AS avg_participants,
                AVG(r.points_total) AS avg_level
            FROM tournaments t
            JOIN results r ON r.tournament_id = t.id
            WHERE t.date IS NOT NULL AND t.date != ''
            GROUP BY SUBSTR(t.date, 1, 7)
            ORDER BY period ASC
            """,
        ).fetchall()
        return [
            TournamentTrendEntry(
                period=str(row[0] or ""),
                tournament_count=int(row[1]),
                avg_participants=float(row[2] or 0),
                avg_level=float(row[3] or 0),
            )
            for row in rows
        ]

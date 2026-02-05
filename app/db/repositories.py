"""SQLite repositories for core entities."""

from __future__ import annotations

import sqlite3
from typing import Any


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


class PlayerRepository:
    """Repository for player data access."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def create(self, data: dict[str, Any]) -> int:
        cursor = self._connection.execute(
            """
            INSERT INTO players (
                last_name,
                first_name,
                middle_name,
                birth_date,
                gender,
                coach,
                club,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("last_name"),
                data.get("first_name"),
                data.get("middle_name"),
                data.get("birth_date"),
                data.get("gender"),
                data.get("coach"),
                data.get("club"),
                data.get("notes"),
            ),
        )
        self._connection.commit()
        return int(cursor.lastrowid)

    def get(self, player_id: int) -> dict[str, Any] | None:
        row = self._connection.execute(
            "SELECT * FROM players WHERE id = ?", (player_id,)
        ).fetchone()
        return _row_to_dict(row)

    def update(self, player_id: int, data: dict[str, Any]) -> None:
        self._connection.execute(
            """
            UPDATE players
            SET last_name = ?,
                first_name = ?,
                middle_name = ?,
                birth_date = ?,
                gender = ?,
                coach = ?,
                club = ?,
                notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                data.get("last_name"),
                data.get("first_name"),
                data.get("middle_name"),
                data.get("birth_date"),
                data.get("gender"),
                data.get("coach"),
                data.get("club"),
                data.get("notes"),
                player_id,
            ),
        )
        self._connection.commit()

    def delete(self, player_id: int) -> None:
        self._connection.execute("DELETE FROM players WHERE id = ?", (player_id,))
        self._connection.commit()

    def list(self) -> list[dict[str, Any]]:
        rows = self._connection.execute(
            "SELECT * FROM players ORDER BY last_name, first_name"
        ).fetchall()
        return [dict(row) for row in rows]

    def search(self, term: str) -> list[dict[str, Any]]:
        like_term = f"%{term}%"
        rows = self._connection.execute(
            """
            SELECT * FROM players
            WHERE last_name LIKE ?
               OR first_name LIKE ?
               OR middle_name LIKE ?
               OR club LIKE ?
               OR coach LIKE ?
            ORDER BY last_name, first_name
            """,
            (like_term, like_term, like_term, like_term, like_term),
        ).fetchall()
        return [dict(row) for row in rows]

    def find_by_identity(
        self,
        *,
        last_name: str,
        first_name: str,
        middle_name: str | None,
        birth_date: str | None,
        birth_year: str | None,
    ) -> dict[str, Any] | None:
        params: list[Any] = [last_name, first_name, middle_name or ""]
        clauses = [
            "last_name = ?",
            "first_name = ?",
            "COALESCE(middle_name, '') = ?",
        ]
        if birth_date:
            clauses.append("birth_date = ?")
            params.append(birth_date)
        elif birth_year:
            clauses.append("(birth_date LIKE ? OR birth_date = ?)")
            params.extend([f"{birth_year}%", birth_year])
        where_sql = " AND ".join(clauses)
        row = self._connection.execute(
            f"SELECT * FROM players WHERE {where_sql} LIMIT 1",
            params,
        ).fetchone()
        return _row_to_dict(row)


class TournamentRepository:
    """Repository for tournament data access."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def create(self, data: dict[str, Any]) -> int:
        cursor = self._connection.execute(
            """
            INSERT INTO tournaments (
                name,
                date,
                category_code,
                league_code,
                source_files
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                data.get("name"),
                data.get("date"),
                data.get("category_code"),
                data.get("league_code"),
                data.get("source_files"),
            ),
        )
        self._connection.commit()
        return int(cursor.lastrowid)

    def get(self, tournament_id: int) -> dict[str, Any] | None:
        row = self._connection.execute(
            "SELECT * FROM tournaments WHERE id = ?", (tournament_id,)
        ).fetchone()
        return _row_to_dict(row)

    def update(self, tournament_id: int, data: dict[str, Any]) -> None:
        self._connection.execute(
            """
            UPDATE tournaments
            SET name = ?,
                date = ?,
                category_code = ?,
                league_code = ?,
                source_files = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                data.get("name"),
                data.get("date"),
                data.get("category_code"),
                data.get("league_code"),
                data.get("source_files"),
                tournament_id,
            ),
        )
        self._connection.commit()

    def delete(self, tournament_id: int) -> None:
        self._connection.execute(
            "DELETE FROM tournaments WHERE id = ?", (tournament_id,)
        )
        self._connection.commit()

    def list(self) -> list[dict[str, Any]]:
        rows = self._connection.execute(
            "SELECT * FROM tournaments ORDER BY date DESC, name"
        ).fetchall()
        return [dict(row) for row in rows]

    def search(self, term: str) -> list[dict[str, Any]]:
        like_term = f"%{term}%"
        rows = self._connection.execute(
            """
            SELECT * FROM tournaments
            WHERE name LIKE ?
               OR category_code LIKE ?
               OR league_code LIKE ?
            ORDER BY date DESC, name
            """,
            (like_term, like_term, like_term),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_latest(self) -> dict[str, Any] | None:
        row = self._connection.execute(
            "SELECT * FROM tournaments ORDER BY date DESC, id DESC LIMIT 1"
        ).fetchone()
        return _row_to_dict(row)

    def list_category_codes(self) -> list[str]:
        rows = self._connection.execute(
            """
            SELECT DISTINCT category_code
            FROM tournaments
            WHERE category_code IS NOT NULL AND category_code != ''
            ORDER BY category_code
            """
        ).fetchall()
        return [str(row[0]) for row in rows]


class ResultRepository:
    """Repository for tournament results data access."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def create(self, data: dict[str, Any]) -> int:
        cursor = self._connection.execute(
            """
            INSERT INTO results (
                tournament_id,
                player_id,
                place,
                score_set,
                score_sector20,
                score_big_round,
                rank_set,
                rank_sector20,
                rank_big_round,
                points_classification,
                points_place,
                points_total,
                calc_version
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("tournament_id"),
                data.get("player_id"),
                data.get("place"),
                data.get("score_set"),
                data.get("score_sector20"),
                data.get("score_big_round"),
                data.get("rank_set"),
                data.get("rank_sector20"),
                data.get("rank_big_round"),
                data.get("points_classification"),
                data.get("points_place"),
                data.get("points_total"),
                data.get("calc_version"),
            ),
        )
        self._connection.commit()
        return int(cursor.lastrowid)

    def get(self, result_id: int) -> dict[str, Any] | None:
        row = self._connection.execute(
            "SELECT * FROM results WHERE id = ?", (result_id,)
        ).fetchone()
        return _row_to_dict(row)

    def update(self, result_id: int, data: dict[str, Any]) -> None:
        self._connection.execute(
            """
            UPDATE results
            SET tournament_id = ?,
                player_id = ?,
                place = ?,
                score_set = ?,
                score_sector20 = ?,
                score_big_round = ?,
                rank_set = ?,
                rank_sector20 = ?,
                rank_big_round = ?,
                points_classification = ?,
                points_place = ?,
                points_total = ?,
                calc_version = ?
            WHERE id = ?
            """,
            (
                data.get("tournament_id"),
                data.get("player_id"),
                data.get("place"),
                data.get("score_set"),
                data.get("score_sector20"),
                data.get("score_big_round"),
                data.get("rank_set"),
                data.get("rank_sector20"),
                data.get("rank_big_round"),
                data.get("points_classification"),
                data.get("points_place"),
                data.get("points_total"),
                data.get("calc_version"),
                result_id,
            ),
        )
        self._connection.commit()

    def delete(self, result_id: int) -> None:
        self._connection.execute("DELETE FROM results WHERE id = ?", (result_id,))
        self._connection.commit()

    def list(self) -> list[dict[str, Any]]:
        rows = self._connection.execute(
            "SELECT * FROM results ORDER BY points_total DESC, place ASC"
        ).fetchall()
        return [dict(row) for row in rows]

    def search(
        self, *, tournament_id: int | None = None, player_id: int | None = None
    ) -> list[dict[str, Any]]:
        clauses = []
        params: list[Any] = []
        if tournament_id is not None:
            clauses.append("tournament_id = ?")
            params.append(tournament_id)
        if player_id is not None:
            clauses.append("player_id = ?")
            params.append(player_id)

        where_sql = ""
        if clauses:
            where_sql = "WHERE " + " AND ".join(clauses)

        rows = self._connection.execute(
            f"SELECT * FROM results {where_sql} ORDER BY points_total DESC, place ASC",
            params,
        ).fetchall()
        return [dict(row) for row in rows]

    def list_with_players(self, tournament_id: int) -> list[dict[str, Any]]:
        rows = self._connection.execute(
            """
            SELECT results.*,
                   players.last_name,
                   players.first_name,
                   players.middle_name,
                   players.birth_date,
                   players.gender
            FROM results
            JOIN players ON players.id = results.player_id
            WHERE results.tournament_id = ?
            ORDER BY results.points_total DESC, results.place ASC
            """,
            (tournament_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def list_results_for_rating(
        self,
        *,
        category_code: str | None = None,
        search_term: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if category_code:
            clauses.append("tournaments.category_code = ?")
            params.append(category_code)

        if search_term:
            like_term = f"%{search_term}%"
            clauses.append(
                "(players.last_name LIKE ? OR players.first_name LIKE ? OR players.middle_name LIKE ?)"
            )
            params.extend([like_term, like_term, like_term])

        where_sql = ""
        if clauses:
            where_sql = "WHERE " + " AND ".join(clauses)

        rows = self._connection.execute(
            f"""
            SELECT results.player_id,
                   results.points_total,
                   tournaments.date AS tournament_date,
                   players.last_name,
                   players.first_name,
                   players.middle_name
            FROM results
            JOIN tournaments ON tournaments.id = results.tournament_id
            JOIN players ON players.id = results.player_id
            {where_sql}
            ORDER BY tournaments.date DESC, tournaments.id DESC
            """,
            params,
        ).fetchall()
        return [dict(row) for row in rows]

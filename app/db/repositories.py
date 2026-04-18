"""SQLite repositories for core entities."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from typing import Any, List

from app.domain.tournament_lifecycle import (
    TournamentStatus,
    allowed_targets,
    can_transition,
)


RowDict = dict[str, Any]
RowMapper = Callable[[sqlite3.Row], RowDict]

TOURNAMENT_STATUS_DRAFT = TournamentStatus.DRAFT.value
TOURNAMENT_STATUS_REVIEW = TournamentStatus.REVIEW.value
TOURNAMENT_STATUS_PUBLISHED = TournamentStatus.PUBLISHED.value
TOURNAMENT_STATUS_CONFIRMED = TournamentStatus.CONFIRMED.value
TOURNAMENT_STATUS_ARCHIVED = TournamentStatus.ARCHIVED.value
TOURNAMENT_STATUS_CANCELED = TournamentStatus.CANCELED.value

TOURNAMENT_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    status.value: allowed_targets(status)
    for status in TournamentStatus
}

TOURNAMENT_LIFECYCLE_DEFAULTS: dict[str, Any] = {
    "status": TOURNAMENT_STATUS_DRAFT,
    "type": "standard",
    "season": None,
    "series": None,
    "location": None,
    "organizer": None,
    "description": None,
    "published_by": None,
    "confirmed_by": None,
    "has_draft_changes": 1,
    "warning_state": "none",
    "error_state": "none",
}


def _row_to_dict(row: sqlite3.Row | None, mapper: RowMapper = dict) -> RowDict | None:
    if row is None:
        return None
    return mapper(row)


def _lastrowid_as_int(cursor: sqlite3.Cursor) -> int:
    lastrowid = cursor.lastrowid
    if lastrowid is None:
        raise RuntimeError("SQLite cursor has no lastrowid after INSERT")
    if isinstance(lastrowid, int):
        return lastrowid
    return int(lastrowid)


def _normalize_tournament_row(row: sqlite3.Row) -> RowDict:
    data = dict(row)
    for field, default in TOURNAMENT_LIFECYCLE_DEFAULTS.items():
        value = data.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            data[field] = default
    return data


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
        return _lastrowid_as_int(cursor)

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

    def search(self, term: str) -> List[RowDict]:
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
        payload = {**TOURNAMENT_LIFECYCLE_DEFAULTS, **data}
        cursor = self._connection.execute(
            """
            INSERT INTO tournaments (
                name,
                date,
                category_code,
                league_code,
                source_files,
                status,
                type,
                season,
                series,
                location,
                organizer,
                description,
                published_by,
                confirmed_by,
                has_draft_changes,
                warning_state,
                error_state
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.get("name"),
                payload.get("date"),
                payload.get("category_code"),
                payload.get("league_code"),
                payload.get("source_files"),
                payload.get("status"),
                payload.get("type"),
                payload.get("season"),
                payload.get("series"),
                payload.get("location"),
                payload.get("organizer"),
                payload.get("description"),
                payload.get("published_by"),
                payload.get("confirmed_by"),
                payload.get("has_draft_changes"),
                payload.get("warning_state"),
                payload.get("error_state"),
            ),
        )
        self._connection.commit()
        return _lastrowid_as_int(cursor)

    def get(self, tournament_id: int) -> dict[str, Any] | None:
        row = self._connection.execute(
            "SELECT * FROM tournaments WHERE id = ?", (tournament_id,)
        ).fetchone()
        return _row_to_dict(row, _normalize_tournament_row)

    def update(self, tournament_id: int, data: dict[str, Any]) -> None:
        payload = {**TOURNAMENT_LIFECYCLE_DEFAULTS, **data}
        self._connection.execute(
            """
            UPDATE tournaments
            SET name = ?,
                date = ?,
                category_code = ?,
                league_code = ?,
                source_files = ?,
                type = ?,
                season = ?,
                series = ?,
                location = ?,
                organizer = ?,
                description = ?,
                published_by = ?,
                confirmed_by = ?,
                has_draft_changes = ?,
                warning_state = ?,
                error_state = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                payload.get("name"),
                payload.get("date"),
                payload.get("category_code"),
                payload.get("league_code"),
                payload.get("source_files"),
                payload.get("type"),
                payload.get("season"),
                payload.get("series"),
                payload.get("location"),
                payload.get("organizer"),
                payload.get("description"),
                payload.get("published_by"),
                payload.get("confirmed_by"),
                payload.get("has_draft_changes"),
                payload.get("warning_state"),
                payload.get("error_state"),
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
        return [_normalize_tournament_row(row) for row in rows]

    def search(self, term: str) -> List[RowDict]:
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
        return _row_to_dict(row, _normalize_tournament_row)

    def set_status(
        self,
        tournament_id: int,
        status: str,
        *,
        actor: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        current = self.get(tournament_id)
        if current is None:
            raise ValueError(f"Tournament with id={tournament_id} does not exist")

        current_status = str(current.get("status") or TOURNAMENT_STATUS_DRAFT)
        if status not in TOURNAMENT_ALLOWED_TRANSITIONS:
            raise ValueError(f"Unknown tournament status: {status}")

        if status == current_status:
            return

        if not can_transition(current_status, status, context):
            raise ValueError(
                f"Invalid tournament status transition: {current_status} -> {status}"
            )

        published_by = current.get("published_by")
        confirmed_by = current.get("confirmed_by")
        if status == TOURNAMENT_STATUS_PUBLISHED:
            published_by = actor or published_by
        if status == TOURNAMENT_STATUS_CONFIRMED:
            confirmed_by = actor or confirmed_by

        self._connection.execute(
            """
            UPDATE tournaments
            SET status = ?,
                published_by = ?,
                confirmed_by = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, published_by, confirmed_by, tournament_id),
        )
        self._connection.commit()

    def publish(self, tournament_id: int, *, actor: str | None = None) -> None:
        self.set_status(tournament_id, TOURNAMENT_STATUS_PUBLISHED, actor=actor)

    def confirm(self, tournament_id: int, *, actor: str | None = None) -> None:
        self.set_status(tournament_id, TOURNAMENT_STATUS_CONFIRMED, actor=actor)

    def archive(self, tournament_id: int, *, actor: str | None = None) -> None:
        self.set_status(tournament_id, TOURNAMENT_STATUS_ARCHIVED, actor=actor)

    def cancel(self, tournament_id: int, *, actor: str | None = None) -> None:
        self.set_status(tournament_id, TOURNAMENT_STATUS_CANCELED, actor=actor)

    def list_category_codes(self) -> List[str]:
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
        return _lastrowid_as_int(cursor)

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
    ) -> List[RowDict]:
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

    def list_with_players(self, tournament_id: int) -> List[RowDict]:
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


    def list_player_history(self, player_id: int) -> List[RowDict]:
        rows = self._connection.execute(
            """
            SELECT results.id,
                   results.tournament_id,
                   results.place,
                   results.points_total,
                   tournaments.name AS tournament_name,
                   tournaments.date AS tournament_date,
                   tournaments.category_code AS category_code
            FROM results
            JOIN tournaments ON tournaments.id = results.tournament_id
            WHERE results.player_id = ?
            ORDER BY tournaments.date DESC, tournaments.id DESC
            """,
            (player_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def list_results_for_rating(
        self,
        *,
        category_code: str | None = None,
        search_term: str | None = None,
    ) -> List[RowDict]:
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

"""SQLite repositories for core entities."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from typing import Any, Iterable, List

from app.domain.rating import normalize_adult_gender_scope
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
    "is_adult_mode": 0,
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
                is_adult_mode,
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.get("name"),
                payload.get("date"),
                payload.get("category_code"),
                payload.get("league_code"),
                payload.get("is_adult_mode"),
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
                is_adult_mode = ?,
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
                payload.get("is_adult_mode"),
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
            WHERE category_code IS NOT NULL
              AND category_code != ''
              AND COALESCE(is_adult_mode, 0) = 0
            ORDER BY category_code
            """
        ).fetchall()
        return [str(row[0]) for row in rows]

    def list_league_codes(self) -> List[str]:
        rows = self._connection.execute(
            """
            SELECT DISTINCT league_code
            FROM tournaments
            WHERE league_code IS NOT NULL AND league_code != ''
            ORDER BY league_code
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
        league_code: str | None = None,
        is_adult_mode: bool | None = None,
        adult_gender_scope: str | None = None,
        search_term: str | None = None,
        statuses: Iterable[str] | None = None,
    ) -> List[RowDict]:
        clauses: list[str] = []
        params: list[Any] = []
        status_values = list(statuses) if statuses is not None else [TOURNAMENT_STATUS_PUBLISHED]
        if not status_values:
            return []

        status_placeholders = ", ".join("?" for _ in status_values)
        clauses.append(f"tournaments.status IN ({status_placeholders})")
        params.extend(status_values)
        if category_code:
            clauses.append("tournaments.category_code = ?")
            params.append(category_code)
        if league_code:
            clauses.append("tournaments.league_code = ?")
            params.append(league_code)
        if adult_gender_scope is not None and is_adult_mode is None:
            is_adult_mode = True
        if is_adult_mode is None and category_code:
            is_adult_mode = False
        if is_adult_mode is not None:
            clauses.append("COALESCE(tournaments.is_adult_mode, 0) = ?")
            params.append(1 if is_adult_mode else 0)

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
                   results.tournament_id,
                   results.points_total,
                   tournaments.date AS tournament_date,
                   tournaments.status AS tournament_status,
                   players.last_name,
                   players.first_name,
                   players.middle_name,
                   players.gender
            FROM results
            JOIN tournaments ON tournaments.id = results.tournament_id
            JOIN players ON players.id = results.player_id
            {where_sql}
            ORDER BY tournaments.date DESC, tournaments.id DESC
            """,
            params,
        ).fetchall()
        result_rows = [dict(row) for row in rows]
        normalized_scope = str(adult_gender_scope or "").strip().lower() or None
        if normalized_scope not in {None, "overall", "men", "women"}:
            return []
        if normalized_scope in {"men", "women"}:
            result_rows = [
                row
                for row in result_rows
                if normalize_adult_gender_scope(row.get("gender")) == normalized_scope
            ]
        return result_rows


class RatingSnapshotRepository:
    """Repository for persisted rating snapshot rows."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def create_many(self, entries: list[dict[str, Any]]) -> int:
        if not entries:
            return 0
        with self._connection:
            self._connection.executemany(
                """
                INSERT INTO rating_snapshots (
                    scope_type,
                    scope_key,
                    player_id,
                    position,
                    points,
                    tournaments_count,
                    rolling_basis_json,
                    source_tournament_id,
                    reason,
                    operation_group_id,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        entry.get("scope_type"),
                        entry.get("scope_key"),
                        entry.get("player_id"),
                        entry.get("position"),
                        entry.get("points"),
                        entry.get("tournaments_count"),
                        entry.get("rolling_basis_json"),
                        entry.get("source_tournament_id"),
                        entry.get("reason"),
                        entry.get("operation_group_id"),
                        entry.get("created_at"),
                    )
                    for entry in entries
                ],
            )
        return len(entries)

    def list_sessions(self, *, scope_type: str, scope_key: str) -> List[RowDict]:
        rows = self._connection.execute(
            """
            SELECT
                created_at,
                scope_type,
                scope_key,
                source_tournament_id,
                reason,
                operation_group_id,
                COUNT(*) AS entries_count
            FROM rating_snapshots
            WHERE scope_type = ? AND scope_key = ?
            GROUP BY
                created_at,
                scope_type,
                scope_key,
                source_tournament_id,
                reason,
                operation_group_id
            ORDER BY created_at DESC
            """,
            (scope_type, scope_key),
        ).fetchall()
        return [dict(row) for row in rows]

    def list_rows(
        self,
        *,
        snapshot_created_at: str,
        scope_type: str,
        scope_key: str,
    ) -> List[RowDict]:
        rows = self._connection.execute(
            """
            SELECT
                rating_snapshots.*,
                players.last_name,
                players.first_name,
                players.middle_name
            FROM rating_snapshots
            JOIN players ON players.id = rating_snapshots.player_id
            WHERE rating_snapshots.created_at = ?
              AND rating_snapshots.scope_type = ?
              AND rating_snapshots.scope_key = ?
            ORDER BY rating_snapshots.position ASC, rating_snapshots.id ASC
            """,
            (snapshot_created_at, scope_type, scope_key),
        ).fetchall()
        return [dict(row) for row in rows]

    def list_latest_rows_for_player(self, player_id: int) -> List[RowDict]:
        rows = self._connection.execute(
            """
            SELECT
                rating_snapshots.*,
                players.last_name,
                players.first_name,
                players.middle_name
            FROM rating_snapshots
            JOIN players ON players.id = rating_snapshots.player_id
            JOIN (
                SELECT
                    scope_type,
                    scope_key,
                    MAX(created_at) AS latest_created_at
                FROM rating_snapshots
                WHERE player_id = ?
                GROUP BY scope_type, scope_key
            ) latest
              ON latest.scope_type = rating_snapshots.scope_type
             AND latest.scope_key = rating_snapshots.scope_key
             AND latest.latest_created_at = rating_snapshots.created_at
            WHERE rating_snapshots.player_id = ?
            ORDER BY rating_snapshots.scope_type ASC, rating_snapshots.scope_key ASC
            """,
            (player_id, player_id),
        ).fetchall()
        return [dict(row) for row in rows]


class LeagueTransferRepository:
    """Repository for persisted league transfer events."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def create_many(self, entries: list[dict[str, Any]]) -> int:
        if not entries:
            return 0
        with self._connection:
            self._connection.executemany(
                """
                INSERT INTO league_transfer_events (
                    player_id,
                    from_league_code,
                    to_league_code,
                    source_tournament_id,
                    reason,
                    operation_group_id,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        entry.get("player_id"),
                        entry.get("from_league_code"),
                        entry.get("to_league_code"),
                        entry.get("source_tournament_id"),
                        entry.get("reason"),
                        entry.get("operation_group_id"),
                        entry.get("created_at"),
                    )
                    for entry in entries
                ],
            )
        return len(entries)

    def get_latest_for_player(self, player_id: int) -> RowDict | None:
        row = self._connection.execute(
            """
            SELECT *
            FROM league_transfer_events
            WHERE player_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (player_id,),
        ).fetchone()
        return None if row is None else dict(row)

    def list_for_player(self, player_id: int) -> List[RowDict]:
        rows = self._connection.execute(
            """
            SELECT
                league_transfer_events.*,
                tournaments.name AS tournament_name,
                tournaments.date AS tournament_date
            FROM league_transfer_events
            JOIN tournaments ON tournaments.id = league_transfer_events.source_tournament_id
            WHERE league_transfer_events.player_id = ?
            ORDER BY league_transfer_events.created_at DESC, league_transfer_events.id DESC
            """,
            (player_id,),
        ).fetchall()
        return [dict(row) for row in rows]


class NoteRepository:
    """Repository for first-class notes attached to entities."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def create(self, data: dict[str, Any]) -> int:
        cursor = self._connection.execute(
            """
            INSERT INTO notes (
                entity_type,
                entity_id,
                note_type,
                visibility,
                author,
                title,
                body,
                priority,
                is_pinned,
                is_archived
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("entity_type"),
                data.get("entity_id"),
                data.get("note_type"),
                data.get("visibility"),
                data.get("author"),
                data.get("title"),
                data.get("body"),
                data.get("priority"),
                int(bool(data.get("is_pinned"))),
                int(bool(data.get("is_archived"))),
            ),
        )
        self._connection.commit()
        return _lastrowid_as_int(cursor)

    def list_for_entity(
        self,
        *,
        entity_type: str,
        entity_id: str,
        include_archived: bool = False,
        note_types: list[str] | None = None,
        visibilities: list[str] | None = None,
        query: str | None = None,
    ) -> List[RowDict]:
        clauses = ["entity_type = ?", "entity_id = ?"]
        params: list[Any] = [entity_type, entity_id]
        if not include_archived:
            clauses.append("is_archived = 0")
        if note_types:
            placeholders = ", ".join("?" for _ in note_types)
            clauses.append(f"note_type IN ({placeholders})")
            params.extend(note_types)
        if visibilities:
            placeholders = ", ".join("?" for _ in visibilities)
            clauses.append(f"visibility IN ({placeholders})")
            params.extend(visibilities)
        normalized_query = (query or "").strip()
        if normalized_query:
            like_value = f"%{normalized_query}%"
            clauses.append("(title LIKE ? OR body LIKE ?)")
            params.extend([like_value, like_value])
        rows = self._connection.execute(
            f"""
            SELECT *
            FROM notes
            WHERE {' AND '.join(clauses)}
            ORDER BY is_pinned DESC, created_at DESC, id DESC
            """,
            params,
        ).fetchall()
        return [dict(row) for row in rows]

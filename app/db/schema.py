"""Database schema definitions."""

from __future__ import annotations

import sqlite3

PLAYER_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    last_name TEXT NOT NULL,
    first_name TEXT NOT NULL,
    middle_name TEXT,
    birth_date TEXT,
    gender TEXT,
    coach TEXT,
    club TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

PLAYER_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_players_name ON players (last_name, first_name);",
    "CREATE INDEX IF NOT EXISTS idx_players_birth_date ON players (birth_date);",
]

TOURNAMENT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS tournaments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    date TEXT,
    category_code TEXT,
    league_code TEXT,
    source_files TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    type TEXT NOT NULL DEFAULT 'standard',
    season TEXT,
    series TEXT,
    location TEXT,
    organizer TEXT,
    description TEXT,
    published_by TEXT,
    confirmed_by TEXT,
    has_draft_changes INTEGER NOT NULL DEFAULT 1,
    warning_state TEXT NOT NULL DEFAULT 'none',
    error_state TEXT NOT NULL DEFAULT 'none',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

RESULT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    place INTEGER,
    score_set INTEGER,
    score_sector20 INTEGER,
    score_big_round INTEGER,
    rank_set TEXT,
    rank_sector20 TEXT,
    rank_big_round TEXT,
    points_classification INTEGER,
    points_place INTEGER,
    points_total INTEGER,
    calc_version TEXT,
    UNIQUE (tournament_id, player_id),
    CHECK (place >= 1 OR place IS NULL),
    FOREIGN KEY (tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
);
"""

RESULT_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_results_tournament ON results (tournament_id);",
    "CREATE INDEX IF NOT EXISTS idx_results_player ON results (player_id);",
]

AUDIT_LOG_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    title TEXT NOT NULL,
    details TEXT,
    level TEXT NOT NULL DEFAULT 'info',
    context_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

AUDIT_LOG_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log (created_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_audit_log_event_type ON audit_log (event_type);",
]


SCHEMA_SQL = [
    PLAYER_TABLE_SQL,
    TOURNAMENT_TABLE_SQL,
    RESULT_TABLE_SQL,
    AUDIT_LOG_TABLE_SQL,
    *PLAYER_INDEXES_SQL,
    *RESULT_INDEXES_SQL,
    *AUDIT_LOG_INDEXES_SQL,
]

TOURNAMENT_LIFECYCLE_COLUMNS: list[tuple[str, str]] = [
    ("status", "TEXT NOT NULL DEFAULT 'draft'"),
    ("type", "TEXT NOT NULL DEFAULT 'standard'"),
    ("season", "TEXT"),
    ("series", "TEXT"),
    ("location", "TEXT"),
    ("organizer", "TEXT"),
    ("description", "TEXT"),
    ("published_by", "TEXT"),
    ("confirmed_by", "TEXT"),
    ("has_draft_changes", "INTEGER NOT NULL DEFAULT 1"),
    ("warning_state", "TEXT NOT NULL DEFAULT 'none'"),
    ("error_state", "TEXT NOT NULL DEFAULT 'none'"),
]


def _column_exists(
    connection: sqlite3.Connection, *, table: str, column: str
) -> bool:
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in rows)


def _migrate_tournaments_schema(connection: sqlite3.Connection) -> None:
    for column_name, column_sql in TOURNAMENT_LIFECYCLE_COLUMNS:
        if _column_exists(connection, table="tournaments", column=column_name):
            continue
        connection.execute(
            f"ALTER TABLE tournaments ADD COLUMN {column_name} {column_sql}"
        )

    connection.execute(
        """
        UPDATE tournaments
        SET status = COALESCE(NULLIF(status, ''), 'draft'),
            type = COALESCE(NULLIF(type, ''), 'standard'),
            has_draft_changes = COALESCE(has_draft_changes, 1),
            warning_state = COALESCE(NULLIF(warning_state, ''), 'none'),
            error_state = COALESCE(NULLIF(error_state, ''), 'none')
        """
    )


def initialize_schema(connection: sqlite3.Connection) -> None:
    """Initialize database schema if needed."""
    with connection:
        for statement in SCHEMA_SQL:
            connection.execute(statement)
        _migrate_tournaments_schema(connection)

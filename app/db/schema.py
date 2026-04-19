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
    is_adult_mode INTEGER NOT NULL DEFAULT 0,
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

RATING_SNAPSHOTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS rating_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope_type TEXT NOT NULL,
    scope_key TEXT NOT NULL,
    player_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    points INTEGER NOT NULL,
    tournaments_count INTEGER NOT NULL,
    rolling_basis_json TEXT NOT NULL DEFAULT '[]',
    source_tournament_id INTEGER NOT NULL,
    reason TEXT NOT NULL,
    operation_group_id TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    FOREIGN KEY (source_tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE
);
"""

RATING_SNAPSHOTS_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_rating_snapshots_scope_created ON rating_snapshots (scope_type, scope_key, created_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_rating_snapshots_source_tournament ON rating_snapshots (source_tournament_id);",
]

LEAGUE_TRANSFER_EVENTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS league_transfer_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    from_league_code TEXT,
    to_league_code TEXT NOT NULL,
    source_tournament_id INTEGER NOT NULL,
    reason TEXT NOT NULL,
    operation_group_id TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    FOREIGN KEY (source_tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE
);
"""

LEAGUE_TRANSFER_EVENTS_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_league_transfer_events_player_created ON league_transfer_events (player_id, created_at DESC, id DESC);",
    "CREATE INDEX IF NOT EXISTS idx_league_transfer_events_tournament ON league_transfer_events (source_tournament_id);",
]

NOTES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    note_type TEXT NOT NULL,
    visibility TEXT NOT NULL,
    author TEXT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'normal',
    is_pinned INTEGER NOT NULL DEFAULT 0,
    is_archived INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

NOTES_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_notes_entity_created ON notes (entity_type, entity_id, is_archived, is_pinned DESC, created_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_notes_created ON notes (created_at DESC);",
]

AUDIT_LOG_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    title TEXT NOT NULL,
    details TEXT,
    level TEXT NOT NULL DEFAULT 'info',
    context_json TEXT NOT NULL DEFAULT '{}',
    entity_type TEXT,
    entity_id TEXT,
    reason TEXT,
    old_value_json TEXT,
    new_value_json TEXT,
    source TEXT,
    operation_group_id TEXT,
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
    RATING_SNAPSHOTS_TABLE_SQL,
    LEAGUE_TRANSFER_EVENTS_TABLE_SQL,
    NOTES_TABLE_SQL,
    AUDIT_LOG_TABLE_SQL,
    *PLAYER_INDEXES_SQL,
    *RESULT_INDEXES_SQL,
    *RATING_SNAPSHOTS_INDEXES_SQL,
    *LEAGUE_TRANSFER_EVENTS_INDEXES_SQL,
    *NOTES_INDEXES_SQL,
    *AUDIT_LOG_INDEXES_SQL,
]

TOURNAMENT_LIFECYCLE_COLUMNS: list[tuple[str, str]] = [
    ("is_adult_mode", "INTEGER NOT NULL DEFAULT 0"),
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

AUDIT_LOG_EPIC_COLUMNS: list[tuple[str, str]] = [
    ("entity_type", "TEXT"),
    ("entity_id", "TEXT"),
    ("reason", "TEXT"),
    ("old_value_json", "TEXT"),
    ("new_value_json", "TEXT"),
    ("source", "TEXT"),
    ("operation_group_id", "TEXT"),
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
            is_adult_mode = COALESCE(is_adult_mode, 0),
            type = COALESCE(NULLIF(type, ''), 'standard'),
            has_draft_changes = COALESCE(has_draft_changes, 1),
            warning_state = COALESCE(NULLIF(warning_state, ''), 'none'),
            error_state = COALESCE(NULLIF(error_state, ''), 'none')
        """
    )


def _migrate_audit_log_schema(connection: sqlite3.Connection) -> None:
    for column_name, column_sql in AUDIT_LOG_EPIC_COLUMNS:
        if _column_exists(connection, table="audit_log", column=column_name):
            continue
        connection.execute(f"ALTER TABLE audit_log ADD COLUMN {column_name} {column_sql}")


def initialize_schema(connection: sqlite3.Connection) -> None:
    """Initialize database schema if needed."""
    with connection:
        for statement in SCHEMA_SQL:
            connection.execute(statement)
        _migrate_tournaments_schema(connection)
        _migrate_audit_log_schema(connection)

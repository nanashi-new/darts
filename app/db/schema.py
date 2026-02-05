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


SCHEMA_SQL = [
    PLAYER_TABLE_SQL,
    TOURNAMENT_TABLE_SQL,
    RESULT_TABLE_SQL,
    *PLAYER_INDEXES_SQL,
    *RESULT_INDEXES_SQL,
]


def initialize_schema(connection: sqlite3.Connection) -> None:
    """Initialize database schema if needed."""
    with connection:
        for statement in SCHEMA_SQL:
            connection.execute(statement)

"""SQLite database helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from app.runtime_paths import APP_DIR_NAME, get_runtime_paths

from .schema import initialize_schema


def get_default_database_path() -> Path:
    """Return the default database path."""
    return get_runtime_paths().db_path


def _configure_connection(connection: sqlite3.Connection) -> None:
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Create a SQLite connection and ensure schema exists."""
    if db_path is None:
        db_path = get_default_database_path()
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(str(db_path))
    _configure_connection(connection)
    initialize_schema(connection)
    return connection


def execute_script(connection: sqlite3.Connection, script: Iterable[str]) -> None:
    """Execute SQL statements within a transaction."""
    with connection:
        for statement in script:
            connection.execute(statement)

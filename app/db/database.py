"""SQLite database helpers."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Iterable

from .schema import initialize_schema

APP_DIR_NAME = "Darts"
DB_FILENAME = "app.db"


def get_default_database_path() -> Path:
    """Return the default database path.

    On Windows this points into the user's application data directory.
    """
    if os.name == "nt":
        base_dir = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        if base_dir:
            data_dir = Path(base_dir)
        else:
            data_dir = Path.home() / "AppData" / "Roaming"
    else:
        data_dir = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    app_dir = data_dir / APP_DIR_NAME
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir / DB_FILENAME


def _configure_connection(connection: sqlite3.Connection) -> None:
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Create a SQLite connection and ensure schema exists."""
    if db_path is None:
        db_path = get_default_database_path()

    connection = sqlite3.connect(str(db_path))
    _configure_connection(connection)
    initialize_schema(connection)
    return connection


def execute_script(connection: sqlite3.Connection, script: Iterable[str]) -> None:
    """Execute SQL statements within a transaction."""
    with connection:
        for statement in script:
            connection.execute(statement)

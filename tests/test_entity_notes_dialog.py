from __future__ import annotations

import os

import pytest

from app.db.database import get_connection
from app.services.notes import create_note


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytestmark = pytest.mark.release_smoke


def _is_expected_headless_qt_failure(exc: Exception) -> bool:
    if isinstance(exc, ModuleNotFoundError):
        return True
    message = str(exc).lower()
    markers = (
        "libgl.so.1",
        "libegl.so.1",
        "libxkbcommon.so.0",
        "could not load the qt platform plugin",
        "no qt platform plugin could be initialized",
        "qt.qpa.plugin",
        "xcb",
        "offscreen",
    )
    return isinstance(exc, (ImportError, OSError, RuntimeError)) and any(marker in message for marker in markers)


def _ensure_app() -> object:
    try:
        from PySide6.QtWidgets import QApplication
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_entity_notes_dialog_shows_notes_and_applies_query_filter(tmp_path) -> None:
    try:
        _ensure_app()
        from app.ui.entity_notes_dialog import EntityNotesDialog
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    connection = get_connection(tmp_path / "entity-notes-dialog.db")
    create_note(
        connection=connection,
        entity_type="league",
        entity_id="PREMIER",
        note_type="league_note",
        visibility="internal_service",
        title="League baseline",
        body="Baseline operational note.",
        priority="normal",
        author="tests",
    )
    create_note(
        connection=connection,
        entity_type="league",
        entity_id="PREMIER",
        note_type="follow_up",
        visibility="follow_up",
        title="Venue follow-up",
        body="Need to check venue for finals.",
        priority="high",
        author="tests",
    )

    dialog = EntityNotesDialog(
        connection=connection,
        entity_type="league",
        entity_id="PREMIER",
    )
    assert dialog.notes_table.rowCount() == 2
    dialog.search_input.setText("venue")
    dialog._refresh_notes()
    assert dialog.notes_table.rowCount() == 1

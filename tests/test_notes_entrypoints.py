from __future__ import annotations

import os

import pytest

from app.db.database import get_connection
from app.db.repositories import ResultRepository, TournamentRepository


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


def _create_league_tournament(connection) -> int:
    tournaments = TournamentRepository(connection)
    results = ResultRepository(connection)
    tournament_id = tournaments.create(
        {
            "name": "Notes League Cup",
            "date": "2026-04-27",
            "category_code": "U18",
            "league_code": "PREMIER",
            "source_files": "[]",
            "status": "published",
            "has_draft_changes": 0,
        }
    )
    return tournament_id


def test_tournaments_view_opens_notes_dialog_for_current_tournament(monkeypatch, tmp_path) -> None:
    try:
        _ensure_app()
        from app.ui.tournaments_view import TournamentsView
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    connection = get_connection(tmp_path / "tournament-notes-entrypoint.db")
    tournament_id = _create_league_tournament(connection)
    opened: list[tuple[str, str, str, str]] = []

    class FakeEntityNotesDialog:
        def __init__(self, *, connection, entity_type, entity_id, defaults=None, parent=None) -> None:
            opened.append(
                (
                    entity_type,
                    entity_id,
                    "" if defaults is None else defaults.note_type,
                    "" if defaults is None else defaults.visibility,
                )
            )

        def exec(self) -> int:
            return 0

    monkeypatch.setattr("app.ui.tournaments_view.get_connection", lambda: connection)
    monkeypatch.setattr("app.ui.tournaments_view.EntityNotesDialog", FakeEntityNotesDialog)

    view = TournamentsView()
    view.refresh_latest_tournament(tournament_id)
    view._open_tournament_notes()

    assert opened == [("tournament", str(tournament_id), "tournament_note", "internal_service")]


def test_rating_view_opens_league_notes_only_for_league_scope(monkeypatch, tmp_path) -> None:
    try:
        _ensure_app()
        from app.ui.rating_view import RatingView
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    connection = get_connection(tmp_path / "rating-league-notes-entrypoint.db")
    _create_league_tournament(connection)
    opened: list[tuple[str, str, str, str]] = []

    class FakeEntityNotesDialog:
        def __init__(self, *, connection, entity_type, entity_id, defaults=None, parent=None) -> None:
            opened.append(
                (
                    entity_type,
                    entity_id,
                    "" if defaults is None else defaults.note_type,
                    "" if defaults is None else defaults.visibility,
                )
            )

        def exec(self) -> int:
            return 0

    monkeypatch.setattr("app.ui.rating_view.get_connection", lambda: connection)
    monkeypatch.setattr("app.ui.rating_view.EntityNotesDialog", FakeEntityNotesDialog)

    view = RatingView()
    assert view._league_notes_button.isEnabled() is False

    view._scope_type_combo.setCurrentIndex(view._scope_type_combo.findData("league"))
    view._refresh_scope_key_options()
    view._category_combo.setCurrentIndex(1)
    view._refresh_history_button_state()
    view._refresh_league_notes_button_state()

    assert view._league_notes_button.isEnabled() is True
    view._open_league_notes()
    assert opened == [("league", "PREMIER", "league_note", "internal_service")]

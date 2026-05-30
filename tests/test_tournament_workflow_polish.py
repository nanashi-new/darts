"""Tests for tournament workflow polish (FEAT-005)."""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest


def _is_expected_headless_qt_failure(exc: Exception) -> bool:
    if isinstance(exc, ModuleNotFoundError):
        missing_name = getattr(exc, "name", "")
        return missing_name == "PySide6" or missing_name.startswith("PySide6.")
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
    return isinstance(exc, (ImportError, OSError, RuntimeError)) and any(
        marker in message for marker in markers
    )


def _ensure_app():  # type: ignore[no-untyped-def]
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


def test_tournament_status_icon_returns_emojis() -> None:
    from app.ui.labels import tournament_status_icon

    assert tournament_status_icon("draft") != ""
    assert tournament_status_icon("review") != ""
    assert tournament_status_icon("confirmed") != ""
    assert tournament_status_icon("published") != ""
    assert tournament_status_icon("archived") != ""
    assert tournament_status_icon("canceled") != ""
    assert tournament_status_icon(None) == ""
    assert tournament_status_icon("unknown") == ""


def test_tournament_status_color_returns_hex() -> None:
    from app.ui.labels import tournament_status_color

    for status in ("draft", "review", "confirmed", "published", "archived", "canceled"):
        color = tournament_status_color(status)
        assert color.startswith("#")
        assert len(color) == 7

    # None returns default grey
    assert tournament_status_color(None) == "#9E9E9E"
    # Unknown returns default grey
    assert tournament_status_color("unknown") == "#9E9E9E"


def test_tournaments_view_has_status_filter(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    try:
        _ensure_app()
        from app.ui.tournaments_view import TournamentsView
        from PySide6.QtWidgets import QComboBox

        view = TournamentsView()
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    assert hasattr(view, "status_filter_combo")
    assert isinstance(view.status_filter_combo, QComboBox)
    assert view.status_filter_combo.count() == 7


def test_tournaments_view_has_league_filter(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    try:
        _ensure_app()
        from app.ui.tournaments_view import TournamentsView
        from PySide6.QtWidgets import QComboBox

        view = TournamentsView()
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    assert hasattr(view, "league_filter_combo")
    assert isinstance(view.league_filter_combo, QComboBox)
    assert view.league_filter_combo.count() == 3


def test_tournaments_view_has_splitter(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    try:
        _ensure_app()
        from app.ui.tournaments_view import TournamentsView
        from PySide6.QtWidgets import QSplitter

        view = TournamentsView()
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    splitter = view.findChild(QSplitter, "tournaments_workspace_splitter")
    assert splitter is not None


def test_tournaments_view_has_list_table(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    try:
        _ensure_app()
        from app.ui.tournaments_view import TournamentsView
        from PySide6.QtWidgets import QTableWidget

        view = TournamentsView()
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    table = view.findChild(QTableWidget, "tournaments_list_table")
    assert table is not None
    assert table.columnCount() == 4


def test_tournament_details_has_stepper(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    try:
        _ensure_app()
        from app.ui.tournament_details_dialog import TournamentDetailsDialog
        from PySide6.QtWidgets import QWidget

        tournament = {
            "id": 1,
            "name": "Test",
            "date": "2024-01-01",
            "status": "review",
            "category_code": None,
            "league_code": None,
            "type": "standard",
            "season": None,
            "series": None,
            "location": None,
            "organizer": None,
            "source_files": None,
            "has_draft_changes": False,
            "warning_state": "none",
            "error_state": "none",
            "confirmed_by": None,
            "published_by": None,
        }
        dialog = TournamentDetailsDialog(tournament=tournament)
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    stepper = dialog.findChild(QWidget, "tournament_lifecycle_stepper")
    assert stepper is not None

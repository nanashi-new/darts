from __future__ import annotations

import os

import pytest

from app.settings import load_settings


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytestmark = pytest.mark.release_smoke


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


def test_ui_state_helpers_persist_nested_payload(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))

    from app.ui_state import get_view_state, update_view_state

    update_view_state("players", {"search": "Case"})
    update_view_state("rating", {"scope_type": "adult", "scope_key": "women", "n_value": 8})

    assert get_view_state("players") == {"search": "Case"}
    assert get_view_state("rating") == {"scope_type": "adult", "scope_key": "women", "n_value": 8}
    assert load_settings()["ui_state"]["players"]["search"] == "Case"


def test_views_restore_saved_workspace_state(monkeypatch, tmp_path) -> None:
    try:
        _ensure_app()
        from PySide6.QtWidgets import QWidget
        import app.ui.main_window as main_window_module
        import app.ui.players_view as players_view_module
        import app.ui.rating_view as rating_view_module
        import app.ui.context_view as context_view_module
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))

    from app.db.database import get_connection
    from app.ui_state import update_view_state

    connection = get_connection(tmp_path / "ui-state.db")

    update_view_state("main_window", {"current_tab": "Context"})
    update_view_state("players", {"search": "Saved player"})
    update_view_state(
        "rating",
        {"scope_type": "adult", "scope_key": "women", "search": "Saved rating", "n_value": 9},
    )
    update_view_state(
        "context",
        {
            "current_tab": "Training",
            "notes_search": "note filter",
            "notes_entity_type": "league",
            "notes_type": "coach_note",
            "notes_visibility": "coach_only",
            "coach_only": True,
            "training_search": "training filter",
        },
    )

    monkeypatch.setattr(players_view_module, "get_connection", lambda: connection)
    monkeypatch.setattr(rating_view_module, "get_connection", lambda: connection)
    monkeypatch.setattr(context_view_module, "get_connection", lambda: connection)

    class _StubView(QWidget):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__()

    monkeypatch.setattr(main_window_module, "DashboardView", _StubView)
    monkeypatch.setattr(main_window_module, "RatingView", rating_view_module.RatingView)
    monkeypatch.setattr(main_window_module, "TournamentsView", _StubView)
    monkeypatch.setattr(main_window_module, "PlayersView", players_view_module.PlayersView)
    monkeypatch.setattr(main_window_module, "ContextView", context_view_module.ContextView)
    monkeypatch.setattr(main_window_module, "ImportExportView", _StubView)
    monkeypatch.setattr(main_window_module, "ReportsView", _StubView)
    monkeypatch.setattr(main_window_module, "DiagnosticsView", _StubView)
    monkeypatch.setattr(main_window_module, "FaqView", _StubView)
    monkeypatch.setattr(main_window_module, "SettingsView", _StubView)
    monkeypatch.setattr(main_window_module, "AboutView", _StubView)

    window = main_window_module.MainWindow()
    tabs = window.centralWidget()

    assert tabs.tabText(tabs.currentIndex()) == "Контекст"

    rating_view = window.findChild(rating_view_module.RatingView)
    assert rating_view is not None
    assert rating_view._selected_scope_type() == "adult"
    assert rating_view._category_combo.currentData() == "women"
    assert rating_view._search_input.text() == "Saved rating"
    assert rating_view._n_spin.value() == 9

    players_view = window.findChild(players_view_module.PlayersView)
    assert players_view is not None
    assert players_view._search_input.text() == "Saved player"

    context_view = window.findChild(context_view_module.ContextView)
    assert context_view is not None
    assert context_view._tabs.tabText(context_view._tabs.currentIndex()) == "Тренировки"
    assert context_view.notes_search_input.text() == "note filter"
    assert context_view.notes_entity_filter.currentData() == "league"
    assert context_view.notes_type_filter.currentData() == "coach_note"
    assert context_view.notes_visibility_filter.currentData() == "coach_only"
    assert context_view.coach_only_checkbox.isChecked() is True
    assert context_view.training_search_input.text() == "training filter"

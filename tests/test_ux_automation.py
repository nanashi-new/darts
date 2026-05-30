"""Tests for UX automation features: undo, shortcuts, toast, session filters."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


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


# --- UndoManager tests ---


def test_undo_manager_push_and_undo() -> None:
    from app.services.undo_manager import UndoManager

    manager = UndoManager()
    executed: list[str] = []

    manager.push_action("delete", lambda: executed.append("restored"), "Удалить игрока")
    assert manager.can_undo() is True

    desc = manager.undo()
    assert desc == "Удалить игрока"
    assert executed == ["restored"]
    assert manager.can_undo() is False


def test_undo_manager_max_stack_limit() -> None:
    from app.services.undo_manager import UndoManager

    manager = UndoManager()

    for i in range(25):
        manager.push_action("test", lambda: None, f"Action {i}")

    # Only 20 should remain
    count = 0
    while manager.can_undo():
        manager.undo()
        count += 1
    assert count == 20


def test_undo_manager_peek_description() -> None:
    from app.services.undo_manager import UndoManager

    manager = UndoManager()
    assert manager.peek_description() is None

    manager.push_action("edit", lambda: None, "Изменить заметку")
    assert manager.peek_description() == "Изменить заметку"

    # peek does not pop
    assert manager.can_undo() is True
    assert manager.peek_description() == "Изменить заметку"


def test_undo_manager_undo_empty_returns_none() -> None:
    from app.services.undo_manager import UndoManager

    manager = UndoManager()
    assert manager.undo() is None


# --- Session filters tests ---


def test_session_filters_round_trip(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))

    from app.ui_state import get_session_filters, set_session_filters

    # Initially empty
    assert get_session_filters("players") == {}

    # Set filters
    filters = {"status": "active", "league": "Premier", "page": 2}
    set_session_filters("players", filters)

    # Get returns same data
    result = get_session_filters("players")
    assert result == filters

    # Other view is not affected
    assert get_session_filters("tournaments") == {}


def test_session_filters_overwrite(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))

    from app.ui_state import get_session_filters, set_session_filters

    set_session_filters("ratings", {"scope": "adult"})
    set_session_filters("ratings", {"scope": "junior", "n": 5})

    result = get_session_filters("ratings")
    assert result == {"scope": "junior", "n": 5}


# --- ShortcutManager tests ---


def test_shortcut_manager_instantiation() -> None:
    try:
        _ensure_app()
        from PySide6.QtWidgets import QMainWindow
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    from app.ui.shortcuts import ShortcutManager

    window = QMainWindow()
    manager = ShortcutManager(window)
    # Should have shortcuts registered (at least 9 tab + 5 function)
    assert len(manager._shortcuts) >= 14


# --- ToastNotification tests ---


def test_toast_notification_creation() -> None:
    try:
        _ensure_app()
        from PySide6.QtWidgets import QWidget
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    from app.ui.toast_notification import ToastNotification

    parent = QWidget()
    parent.resize(800, 600)
    toast = ToastNotification.show_toast(parent, "Test message", "info")
    assert toast.isVisible()
    assert "Test message" in toast.text()


def test_toast_notification_levels() -> None:
    try:
        _ensure_app()
        from PySide6.QtWidgets import QWidget
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    from app.ui.toast_notification import ToastNotification

    parent = QWidget()
    parent.resize(800, 600)

    for level in ("info", "warning", "error"):
        toast = ToastNotification.show_toast(parent, f"Level: {level}", level)
        assert toast.isVisible()
        style = toast.styleSheet()
        assert "border-radius" in style

"""Tests for the theme system, status bar, and welcome widget."""

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


def test_theme_manager_get_available_themes() -> None:
    try:
        from app.ui.theme import ThemeManager
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    themes = ThemeManager.get_available_themes()
    assert themes == ["light", "dark"]


def test_theme_manager_apply_light_theme() -> None:
    try:
        from PySide6.QtWidgets import QApplication

        app = _ensure_app()
        assert isinstance(app, QApplication)
        from app.ui.theme import ThemeManager

        ThemeManager.apply_theme(app, "light")
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise


def test_theme_manager_apply_dark_theme() -> None:
    try:
        from PySide6.QtWidgets import QApplication

        app = _ensure_app()
        assert isinstance(app, QApplication)
        from app.ui.theme import ThemeManager

        ThemeManager.apply_theme(app, "dark")
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise


def test_theme_manager_apply_with_accent_and_font() -> None:
    try:
        from PySide6.QtWidgets import QApplication

        app = _ensure_app()
        assert isinstance(app, QApplication)
        from app.ui.theme import ThemeManager

        ThemeManager.apply_theme(app, "light", accent_color="#FF5722", font_size="large")
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise


def test_main_window_has_status_bar(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    try:
        _ensure_app()
        from app.ui.main_window import MainWindow

        window = MainWindow()
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    status_bar = window.statusBar()
    assert status_bar is not None


def test_welcome_widget_shown_on_empty_profile(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    try:
        _ensure_app()
        from app.ui.dashboard_view import DashboardView
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    view = DashboardView()
    # On an empty profile, the stacked widget should show index 0 (welcome)
    assert view._stacked.currentIndex() == 0


def test_welcome_widget_hidden_when_data_exists(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    try:
        _ensure_app()
        from app.db.database import get_connection
        from app.ui.dashboard_view import DashboardView
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    # Insert a player into the database so the profile is not empty
    conn = get_connection()
    conn.execute(
        "INSERT INTO players (first_name, last_name) VALUES (?, ?)",
        ("Тест", "Игрок"),
    )
    conn.commit()

    view = DashboardView()
    # With data, the stacked widget should show index 1 (main content)
    assert view._stacked.currentIndex() == 1

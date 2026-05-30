"""Tests for the interactive user guide feature."""

from __future__ import annotations

import os
from pathlib import Path

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


# --- user_guide.md tests ---


def test_user_guide_file_exists() -> None:
    guide_path = Path(__file__).resolve().parents[1] / "app" / "resources" / "user_guide.md"
    assert guide_path.exists(), "user_guide.md must exist in app/resources/"


def test_user_guide_has_expected_sections() -> None:
    guide_path = Path(__file__).resolve().parents[1] / "app" / "resources" / "user_guide.md"
    content = guide_path.read_text(encoding="utf-8")
    expected_sections = [
        "Начало работы",
        "Управление игроками",
        "Турниры",
        "Рейтинг",
        "Тренерская работа",
        "Резервные копии и безопасность",
        "Настройка внешнего вида",
        "Горячие клавиши и подсказки",
    ]
    for section in expected_sections:
        assert f"## {section}" in content, f"Section '{section}' not found in user_guide.md"


# --- help_context tests ---


def test_help_context_covers_all_tabs() -> None:
    from app.resources.help_context import HELP_CONTEXT

    expected_tabs = [
        "Главная",
        "Рейтинг",
        "Турниры",
        "Игроки",
        "Контекст",
        "Тренер",
        "Аналитика",
        "Импорт/Экспорт",
        "Отчеты",
        "Диагностика",
        "Справка",
        "Настройки",
        "О программе",
    ]
    for tab in expected_tabs:
        assert tab in HELP_CONTEXT, f"Tab '{tab}' not in HELP_CONTEXT"
        assert len(HELP_CONTEXT[tab]) > 20, f"Help text for '{tab}' is too short"


# --- GuidedTour tests ---


def test_guided_tour_steps_not_empty() -> None:
    try:
        from app.ui.guided_tour import DEFAULT_STEPS
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    assert len(DEFAULT_STEPS) >= 5


def test_guided_tour_mark_completed_round_trip(monkeypatch, tmp_path) -> None:
    try:
        from app.ui.guided_tour import is_tour_completed, mark_completed
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))

    assert is_tour_completed() is False
    mark_completed()
    assert is_tour_completed() is True


def test_guided_tour_widget(monkeypatch, tmp_path) -> None:
    try:
        _ensure_app()
        from PySide6.QtWidgets import QWidget
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))

    from app.ui.guided_tour import GuidedTour, is_tour_completed

    parent = QWidget()
    tour = GuidedTour(parent)
    assert len(tour.steps) >= 5

    tour.start_tour()
    assert tour.isVisible()

    tour.next_step()
    assert tour.isVisible()

    tour.skip_tour()
    assert not tour.isVisible()
    assert is_tour_completed() is True


# --- HelpView tests ---


def test_help_view_loads_content(monkeypatch, tmp_path) -> None:
    try:
        _ensure_app()
        from PySide6.QtWidgets import QTextBrowser
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))

    from app.ui.faq_view import HelpView

    view = HelpView()
    guide = view.findChild(QTextBrowser, "faq_guide")
    assert guide is not None
    text = guide.toPlainText()
    assert "Начало работы" in text
    assert "Управление игроками" in text


def test_help_view_search_filters_sections(monkeypatch, tmp_path) -> None:
    try:
        _ensure_app()
        from PySide6.QtWidgets import QLineEdit, QTextBrowser
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))

    from app.ui.faq_view import HelpView

    view = HelpView()
    search = view.findChild(QLineEdit, "help_search_input")
    assert search is not None

    search.setText("Рейтинг")
    guide = view.findChild(QTextBrowser, "faq_guide")
    assert guide is not None
    text = guide.toPlainText()
    assert "Рейтинг" in text
    # Other unrelated sections should not be present
    assert "Горячие клавиши" not in text


def test_help_view_search_empty_restores_full(monkeypatch, tmp_path) -> None:
    try:
        _ensure_app()
        from PySide6.QtWidgets import QLineEdit, QTextBrowser
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))

    from app.ui.faq_view import HelpView

    view = HelpView()
    search = view.findChild(QLineEdit, "help_search_input")
    guide = view.findChild(QTextBrowser, "faq_guide")
    assert search is not None
    assert guide is not None

    search.setText("Рейтинг")
    search.setText("")
    text = guide.toPlainText()
    assert "Горячие клавиши" in text
    assert "Начало работы" in text


# --- Backward compatibility ---


def test_faq_view_alias_works() -> None:
    try:
        from app.ui.faq_view import FaqView, HelpView
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    assert FaqView is HelpView

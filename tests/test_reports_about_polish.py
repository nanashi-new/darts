from __future__ import annotations

import os

import pytest


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


def test_reports_view_uses_compact_scroll_friendly_actions(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    try:
        _ensure_app()
        from PySide6.QtWidgets import QPushButton, QScrollArea
        from app.ui.reports_view import ReportsView
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    view = ReportsView()
    scroll_area = view.findChild(QScrollArea, "reports_scroll_area")
    assert scroll_area is not None
    assert scroll_area.widgetResizable()

    buttons = {button.text(): button for button in view.findChildren(QPushButton)}
    expected_tooltips = {
        "Экспорт": "Выгрузить рейтинги и протоколы в выбранную папку.",
        "Пересчет": "Пересчитать результаты всех турниров.",
        "Журнал": "Открыть журнал действий и ошибок.",
        "Импорты": "Открыть историю импортов.",
    }
    for text, tooltip in expected_tooltips.items():
        assert text in buttons
        assert buttons[text].toolTip() == tooltip
        assert len(text) <= 8

    assert "История импортов" not in buttons


def test_about_view_is_scroll_friendly_and_uses_current_brand() -> None:
    try:
        _ensure_app()
        from PySide6.QtWidgets import QLabel, QScrollArea
        from app.ui.about_view import AboutView
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    view = AboutView()
    scroll_area = view.findChild(QScrollArea, "about_scroll_area")
    assert scroll_area is not None
    assert scroll_area.widgetResizable()

    labels = view.findChildren(QLabel)
    visible_text = "\n".join(label.text() for label in labels)
    assert "Дартс Лига" in visible_text
    assert "Darts Rating" not in visible_text
    assert ("E" + "BCK") not in visible_text
    assert any(
        "Локальное приложение" in label.text() and label.wordWrap()
        for label in labels
    )

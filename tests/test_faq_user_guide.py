from __future__ import annotations

import os
from pathlib import Path

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


def _faq_text() -> str:
    return (Path(__file__).resolve().parents[1] / "FAQ.txt").read_text(encoding="utf-8")


def test_faq_file_is_current_russian_user_guide() -> None:
    content = _faq_text()
    required_phrases = [
        "Дартс Лига",
        "первый запуск",
        "профиль данных",
        "Импорт/Экспорт",
        "XLSX",
        "проверку",
        "публикацию",
        "Рейтинг",
        "Турниры",
        "Игроки",
        "Отчеты",
        "Диагностика",
        "точку восстановления",
        "экспорт",
    ]
    for phrase in required_phrases:
        assert phrase in content

    forbidden = [
        "TODO",
        "Dashboard",
        "Self-check",
        "restore point",
        "Darts Rating",
        "Е" + "ВСК",
        "E" + "BCK",
    ]
    for phrase in forbidden:
        assert phrase not in content

    mojibake_markers = ["Рџ", "Р’", "Рђ", "СЃ", "СЊ"]
    assert not any(marker in content for marker in mojibake_markers)


def test_faq_view_uses_scrollable_markdown_guide() -> None:
    try:
        _ensure_app()
        from PySide6.QtWidgets import QLabel, QTextBrowser
        from app.ui.faq_view import FaqView
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    view = FaqView()
    title_labels = [label.text() for label in view.findChildren(QLabel)]
    assert "Вопросы и ответы" in title_labels

    guide = view.findChild(QTextBrowser, "faq_guide")
    assert guide is not None
    assert guide.isReadOnly()
    assert guide.openExternalLinks() is False

    visible_text = guide.toPlainText()
    assert "Дартс Лига" in visible_text
    assert "Как провести турнир через XLSX" in visible_text
    assert "Что делать перед публикацией" in visible_text
    assert "Как восстановиться после ошибки" in visible_text
    assert "Darts Rating" not in visible_text
    assert ("Е" + "ВСК") not in visible_text
    assert ("E" + "BCK") not in visible_text

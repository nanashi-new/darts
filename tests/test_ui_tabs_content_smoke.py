from __future__ import annotations

import os

import pytest

# Must be configured before first PySide6 import.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


pytestmark = pytest.mark.release_smoke

_PLACEHOLDER_TEXTS = (
    "будет реализован позже",
    "placeholder",
)


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


def _qt_widgets():
    try:
        from PySide6.QtWidgets import QApplication, QLabel, QPlainTextEdit, QTabWidget
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise
    return QApplication, QLabel, QPlainTextEdit, QTabWidget


def _ensure_app() -> object:
    QApplication, _, _, _ = _qt_widgets()
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _collect_tab_text(tab_widget) -> str:
    _, QLabel, QPlainTextEdit, _ = _qt_widgets()
    chunks: list[str] = []
    for label in tab_widget.findChildren(QLabel):
        chunks.append(label.text())
    for plain_text in tab_widget.findChildren(QPlainTextEdit):
        chunks.append(plain_text.toPlainText())
    return "\n".join(chunks).lower()


def test_main_tabs_are_russian_and_not_placeholders(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    try:
        _ensure_app()
        from app.ui.main_window import MainWindow

        window = MainWindow()
        _, _, _, q_tab_widget = _qt_widgets()
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    tabs = window.centralWidget()
    assert isinstance(tabs, q_tab_widget)

    tab_names = [tabs.tabText(index) for index in range(tabs.count())]
    assert tab_names == [
        "Главная",
        "Рейтинг",
        "Турниры",
        "Игроки",
        "Контекст",
        "Импорт/Экспорт",
        "Отчеты",
        "Диагностика",
        "Вопросы и ответы",
        "Настройки",
        "О программе",
    ]

    for index in range(tabs.count()):
        content = _collect_tab_text(tabs.widget(index))
        for placeholder in _PLACEHOLDER_TEXTS:
            assert placeholder not in content

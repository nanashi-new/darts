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


def test_main_workspace_renders_all_tabs_at_release_sizes(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    try:
        app = _ensure_app()
        from PySide6.QtCore import QSize
        from PySide6.QtWidgets import QWidget
        from app.ui.main_window import MainWindow
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    window = MainWindow()
    tabs = window.centralWidget()
    expected_tabs = {
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
    }
    assert {tabs.tabText(index) for index in range(tabs.count())} == expected_tabs

    for width, height in [(1366, 768), (1920, 1080)]:
        window.resize(width, height)
        window.show()
        app.processEvents()
        assert window.minimumSize().width() <= width
        assert window.minimumSize().height() <= height

        for index in range(tabs.count()):
            tabs.setCurrentIndex(index)
            app.processEvents()
            current_tab = tabs.currentWidget()
            assert current_tab.minimumSizeHint().width() <= width, tabs.tabText(index)
            assert current_tab.minimumSizeHint().height() <= height, tabs.tabText(index)
            visible_children = [
                child
                for child in current_tab.findChildren(QWidget)
                if child.isVisible() and child.width() > 0 and child.height() > 0
            ]
            assert visible_children, tabs.tabText(index)

            pixmap = current_tab.grab()
            image = pixmap.toImage()
            assert image.size() == QSize(current_tab.width(), current_tab.height())
            assert not image.isNull(), tabs.tabText(index)

        window_image = window.grab().toImage()
        sampled_colors = {
            window_image.pixelColor(x, y).rgba()
            for x in range(0, window_image.width(), 24)
            for y in range(0, window_image.height(), 24)
        }
        assert len(sampled_colors) >= 2

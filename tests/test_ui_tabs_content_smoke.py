from __future__ import annotations

import os

import pytest



_PLACEHOLDER_TEXTS = (
    "будет реализован позже",
    "placeholder",
)


def _is_expected_headless_qt_failure(exc: Exception) -> bool:
    message = str(exc).lower()
    markers = (
        "libgl.so.1",
        "libegl.so.1",
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
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
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


def test_about_and_faq_tabs_do_not_have_placeholder_text() -> None:
    try:
        _ensure_app()
        from app.ui.main_window import MainWindow

        window = MainWindow()
        _, _, _, QTabWidget = _qt_widgets()
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    tabs = window.centralWidget()
    assert isinstance(tabs, QTabWidget)

    tab_names = [tabs.tabText(index) for index in range(tabs.count())]
    for expected_name in ("О программе", "FAQ"):
        assert expected_name in tab_names
        target_index = tab_names.index(expected_name)
        target_widget = tabs.widget(target_index)
        content = _collect_tab_text(target_widget)
        for placeholder in _PLACEHOLDER_TEXTS:
            assert placeholder not in content

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
        from PySide6.QtWidgets import (
            QApplication,
            QLabel,
            QPlainTextEdit,
            QPushButton,
            QSizePolicy,
            QSplitter,
            QStackedWidget,
            QTableView,
            QTableWidget,
            QWidget,
        )
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise
    return (
        QApplication,
        QLabel,
        QPlainTextEdit,
        QPushButton,
        QSizePolicy,
        QSplitter,
        QStackedWidget,
        QTableView,
        QTableWidget,
        QWidget,
    )


def _ensure_app() -> object:
    QApplication, *_ = _qt_widgets()
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _collect_view_text(view_widget) -> str:
    _, QLabel, QPlainTextEdit, *_ = _qt_widgets()
    chunks: list[str] = []
    for label in view_widget.findChildren(QLabel):
        chunks.append(label.text())
    for plain_text in view_widget.findChildren(QPlainTextEdit):
        chunks.append(plain_text.toPlainText())
    return "\n".join(chunks).lower()


def test_main_tabs_are_russian_and_not_placeholders(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    try:
        _ensure_app()
        from app.ui.main_window import MainWindow

        window = MainWindow()
        _, _, _, _, _, _, q_stacked_widget, _, _, q_widget = _qt_widgets()
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    container = window.centralWidget()
    assert isinstance(container, q_widget)

    stacked = window._stacked
    assert isinstance(stacked, q_stacked_widget)

    # All 13 views must be present
    assert stacked.count() == 13

    expected_keys = [
        "dashboard",
        "rating",
        "tournaments",
        "players",
        "context",
        "coach",
        "analytics",
        "import_export",
        "reports",
        "diagnostics",
        "faq",
        "settings",
        "about",
    ]
    assert list(window._VIEW_KEYS) == expected_keys

    for index in range(stacked.count()):
        content = _collect_view_text(stacked.widget(index))
        for placeholder in _PLACEHOLDER_TEXTS:
            assert placeholder not in content


def test_main_window_uses_maximized_workspace_launch(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    try:
        _ensure_app()
        from PySide6.QtCore import Qt
        from app.ui.main_window import MainWindow

        window = MainWindow()
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    assert window.minimumWidth() >= 1280
    assert window.minimumHeight() >= 720

    window.show_workspace()
    assert window.windowState() & Qt.WindowState.WindowMaximized


def test_main_workspace_tabs_are_configured_for_wide_desktop(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    try:
        _ensure_app()
        from PySide6.QtCore import Qt
        from app.ui.main_window import MainWindow

        window = MainWindow()
        _, _, _, _, q_size_policy, _, q_stacked_widget, _, _, q_widget = _qt_widgets()
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    container = window.centralWidget()
    assert isinstance(container, q_widget)
    assert container.objectName() == "main_container"

    stacked = window._stacked
    assert isinstance(stacked, q_stacked_widget)
    assert stacked.objectName() == "main_workspace_stack"
    assert stacked.sizePolicy().horizontalPolicy() == q_size_policy.Policy.Expanding
    assert stacked.sizePolicy().verticalPolicy() == q_size_policy.Policy.Expanding

    sidebar = window._sidebar
    assert sidebar.objectName() == "sidebar_widget"


def test_core_tabs_expose_wide_workspace_layout_contracts(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    try:
        _ensure_app()
        from PySide6.QtCore import Qt
        from app.ui.main_window import MainWindow

        window = MainWindow()
        _, _, _, _, q_size_policy, q_splitter, _, q_table_view, q_table_widget, q_widget = _qt_widgets()
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    views = window._views

    for view_key in ["dashboard", "rating", "tournaments", "players", "import_export", "diagnostics", "settings"]:
        view = views[view_key]
        policy = view.sizePolicy()
        assert policy.horizontalPolicy() == q_size_policy.Policy.Expanding
        assert policy.verticalPolicy() == q_size_policy.Policy.Expanding

    players_splitter = views["players"].findChild(q_splitter, "players_workspace_splitter")
    assert players_splitter is not None
    assert players_splitter.orientation() == Qt.Orientation.Horizontal

    tournaments_actions = views["tournaments"].findChild(q_widget, "tournaments_workspace_actions")
    assert tournaments_actions is not None

    for view_key in ["dashboard", "rating", "tournaments", "players"]:
        view = views[view_key]
        tables = view.findChildren(q_table_view) + view.findChildren(q_table_widget)
        assert tables, f"{view_key} should expose at least one workspace table"
        assert any(table.sizePolicy().horizontalPolicy() == q_size_policy.Policy.Expanding for table in tables)


def test_polished_tabs_use_short_buttons_with_tooltips(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    try:
        _ensure_app()
        from app.ui.main_window import MainWindow

        window = MainWindow()
        _, _, _, q_push_button, *_ = _qt_widgets()
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    views = window._views

    expected_buttons = {
        "tournaments": {
            "Турнир": "Открыть детали выбранного турнира.",
            "Открыть": "Открыть детали выбранного результата.",
            "Взрослый": "Создать черновик взрослого турнира вручную.",
            "Пересчет": "Пересчитать результаты выбранного турнира.",
            "На проверку": "Отправить выбранный турнир на проверку.",
            "Архив": "Безопасно архивировать выбранный турнир с причиной.",
            "Отменить": "Безопасно отменить выбранный турнир с причиной.",
        },
        "import_export": {
            "Импорт файла": "Выбрать XLSX-файл и пройти предпросмотр перед импортом.",
        },
        "reports": {
            "Экспорт": "Выгрузить рейтинги и протоколы в выбранную папку.",
            "Пересчет": "Пересчитать результаты всех турниров.",
            "Журнал": "Открыть журнал действий и ошибок.",
            "Импорты": "Открыть историю импортов.",
        },
        "diagnostics": {
            "Самопроверка": "Запустить проверку профиля, базы и окружения.",
            "Архив": "Создать диагностический архив для поддержки.",
            "Логи": "Открыть папку с журналами приложения.",
            "Профиль": "Открыть папку текущего профиля.",
            "Точка": "Создать точку восстановления профиля.",
            "Детали": "Открыть детали выбранной точки восстановления.",
            "Восстановить": "Запланировать восстановление из выбранной точки.",
            "Сброс": "Запланировать безопасный сброс профиля.",
        },
    }

    for view_key, button_tooltips in expected_buttons.items():
        view = views[view_key]
        buttons = {button.text(): button for button in view.findChildren(q_push_button)}
        for text, tooltip in button_tooltips.items():
            assert text in buttons
            assert tooltip in buttons[text].toolTip()
            assert len(text) <= 12


def test_import_export_tab_has_no_demo_copy(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    try:
        _ensure_app()
        from app.ui.main_window import MainWindow

        window = MainWindow()
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    content = _collect_view_text(window._views["import_export"])

    assert "\u0434\u0435\u043c\u043e" not in content

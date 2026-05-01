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
            QTabWidget,
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
        QTabWidget,
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


def _collect_tab_text(tab_widget) -> str:
    _, QLabel, QPlainTextEdit, *_ = _qt_widgets()
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
        _, _, _, _, _, _, q_tab_widget, _, _, _ = _qt_widgets()
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
        _, _, _, _, q_size_policy, _, q_tab_widget, _, _, _ = _qt_widgets()
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    tabs = window.centralWidget()
    assert isinstance(tabs, q_tab_widget)
    assert tabs.objectName() == "main_workspace_tabs"
    assert tabs.usesScrollButtons()
    assert tabs.documentMode()
    assert tabs.elideMode() == Qt.TextElideMode.ElideRight
    assert tabs.sizePolicy().horizontalPolicy() == q_size_policy.Policy.Expanding
    assert tabs.sizePolicy().verticalPolicy() == q_size_policy.Policy.Expanding


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

    tabs = window.centralWidget()
    tab_widgets = {tabs.tabText(index): tabs.widget(index) for index in range(tabs.count())}

    for tab_name in ["Главная", "Рейтинг", "Турниры", "Игроки", "Импорт/Экспорт", "Диагностика", "Настройки"]:
        policy = tab_widgets[tab_name].sizePolicy()
        assert policy.horizontalPolicy() == q_size_policy.Policy.Expanding
        assert policy.verticalPolicy() == q_size_policy.Policy.Expanding

    players_splitter = tab_widgets["Игроки"].findChild(q_splitter, "players_workspace_splitter")
    assert players_splitter is not None
    assert players_splitter.orientation() == Qt.Orientation.Horizontal

    tournaments_actions = tab_widgets["Турниры"].findChild(q_widget, "tournaments_workspace_actions")
    assert tournaments_actions is not None

    for tab_name in ["Главная", "Рейтинг", "Турниры", "Игроки"]:
        tables = tab_widgets[tab_name].findChildren(q_table_view) + tab_widgets[tab_name].findChildren(q_table_widget)
        assert tables, f"{tab_name} should expose at least one workspace table"
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

    tabs = window.centralWidget()
    tab_widgets = {tabs.tabText(index): tabs.widget(index) for index in range(tabs.count())}

    expected_buttons = {
        "Главная": {
            "Карточка": "Открыть карточку выбранного игрока из контрольных заметок.",
        },
        "Турниры": {
            "Турнир": "Открыть детали выбранного турнира.",
            "Открыть": "Открыть детали выбранного результата.",
            "Взрослый": "Создать черновик взрослого турнира вручную.",
            "Пересчет": "Пересчитать результаты выбранного турнира.",
            "На проверку": "Отправить выбранный турнир на проверку.",
            "Архив": "Безопасно архивировать выбранный турнир с причиной.",
            "Отменить": "Безопасно отменить выбранный турнир с причиной.",
        },
        "Импорт/Экспорт": {
            "Импорт файла": "Выбрать XLSX-файл и пройти предпросмотр перед импортом.",
        },
        "Отчеты": {
            "Экспорт": "Выгрузить рейтинги и протоколы в выбранную папку.",
            "Пересчет": "Пересчитать результаты всех турниров.",
            "Журнал": "Открыть журнал действий и ошибок.",
            "Импорты": "Открыть историю импортов.",
        },
        "Диагностика": {
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

    for tab_name, button_tooltips in expected_buttons.items():
        buttons = {button.text(): button for button in tab_widgets[tab_name].findChildren(q_push_button)}
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

    tabs = window.centralWidget()
    tab_widgets = {tabs.tabText(index): tabs.widget(index) for index in range(tabs.count())}
    content = _collect_tab_text(tab_widgets["Импорт/Экспорт"])

    assert "демо" not in content

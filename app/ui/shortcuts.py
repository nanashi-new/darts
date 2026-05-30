"""Keyboard shortcut manager for the main window."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QMainWindow

if TYPE_CHECKING:
    pass


class ShortcutManager:
    """Registers keyboard shortcuts on MainWindow."""

    def __init__(self, main_window: QMainWindow) -> None:
        self._main_window = main_window
        self._shortcuts: list[QShortcut] = []
        self._setup_shortcuts()

    def _setup_shortcuts(self) -> None:
        # Ctrl+1..9: switch tabs by index
        for i in range(1, 10):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{i}"), self._main_window)
            idx = i - 1
            shortcut.activated.connect(self._make_tab_switcher(idx))
            self._shortcuts.append(shortcut)

        # Ctrl+I: navigate to import tab
        sc_import = QShortcut(QKeySequence("Ctrl+I"), self._main_window)
        sc_import.activated.connect(lambda: self._activate_tab("Импорт/Экспорт"))
        self._shortcuts.append(sc_import)

        # Ctrl+E: navigate to reports tab
        sc_export = QShortcut(QKeySequence("Ctrl+E"), self._main_window)
        sc_export.activated.connect(lambda: self._activate_tab("Отчеты"))
        self._shortcuts.append(sc_export)

        # F1: open help/Справка tab
        sc_help = QShortcut(QKeySequence("F1"), self._main_window)
        sc_help.activated.connect(lambda: self._activate_tab("Справка"))
        self._shortcuts.append(sc_help)

        # Ctrl+S: create backup
        sc_backup = QShortcut(QKeySequence("Ctrl+S"), self._main_window)
        sc_backup.activated.connect(self._trigger_backup)
        self._shortcuts.append(sc_backup)

        # Ctrl+Z: undo
        sc_undo = QShortcut(QKeySequence("Ctrl+Z"), self._main_window)
        sc_undo.activated.connect(self._trigger_undo)
        self._shortcuts.append(sc_undo)

    def _make_tab_switcher(self, index: int):  # type: ignore[no-untyped-def]
        def _switch() -> None:
            tabs = getattr(self._main_window, "_tabs", None)
            if tabs is not None and index < tabs.count():
                tabs.setCurrentIndex(index)

        return _switch

    def _activate_tab(self, target: str) -> None:
        tabs = getattr(self._main_window, "_tabs", None)
        if tabs is None:
            return
        for i in range(tabs.count()):
            if tabs.tabText(i) == target:
                tabs.setCurrentIndex(i)
                return

    def _trigger_backup(self) -> None:
        from app.services.backup_restore import create_backup

        try:
            create_backup()
        except Exception:  # noqa: BLE001
            pass

    def _trigger_undo(self) -> None:
        from app.services.undo_manager import undo_manager

        result = undo_manager.undo()
        if result is not None:
            toast_fn = getattr(self._main_window, "show_toast", None)
            if callable(toast_fn):
                toast_fn(f"Отменено: {result}", "info")

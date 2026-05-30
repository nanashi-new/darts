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
        # Ctrl+1..5: switch sidebar groups
        for i in range(1, 6):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{i}"), self._main_window)
            idx = i - 1
            shortcut.activated.connect(self._make_group_switcher(idx))
            self._shortcuts.append(shortcut)

        # Ctrl+Shift+1..9: switch sub-items within the active group
        for i in range(1, 10):
            shortcut = QShortcut(QKeySequence(f"Ctrl+Shift+{i}"), self._main_window)
            sub_idx = i - 1
            shortcut.activated.connect(self._make_sub_item_switcher(sub_idx))
            self._shortcuts.append(shortcut)

        # Ctrl+I: navigate to import view
        sc_import = QShortcut(QKeySequence("Ctrl+I"), self._main_window)
        sc_import.activated.connect(lambda: self._activate_tab("\u0418\u043c\u043f\u043e\u0440\u0442/\u042d\u043a\u0441\u043f\u043e\u0440\u0442"))
        self._shortcuts.append(sc_import)

        # Ctrl+E: navigate to reports view
        sc_export = QShortcut(QKeySequence("Ctrl+E"), self._main_window)
        sc_export.activated.connect(lambda: self._activate_tab("\u041e\u0442\u0447\u0435\u0442\u044b"))
        self._shortcuts.append(sc_export)

        # F1: open help/Справка view
        sc_help = QShortcut(QKeySequence("F1"), self._main_window)
        sc_help.activated.connect(lambda: self._activate_tab("\u0421\u043f\u0440\u0430\u0432\u043a\u0430"))
        self._shortcuts.append(sc_help)

        # Ctrl+S: create backup
        sc_backup = QShortcut(QKeySequence("Ctrl+S"), self._main_window)
        sc_backup.activated.connect(self._trigger_backup)
        self._shortcuts.append(sc_backup)

        # Ctrl+Z: undo
        sc_undo = QShortcut(QKeySequence("Ctrl+Z"), self._main_window)
        sc_undo.activated.connect(self._trigger_undo)
        self._shortcuts.append(sc_undo)

    def _make_group_switcher(self, group_index: int):  # type: ignore[no-untyped-def]
        def _switch() -> None:
            sidebar = getattr(self._main_window, "_sidebar", None)
            if sidebar is not None:
                sidebar.activate_group(group_index)

        return _switch

    def _make_sub_item_switcher(self, sub_index: int):  # type: ignore[no-untyped-def]
        def _switch() -> None:
            sidebar = getattr(self._main_window, "_sidebar", None)
            if sidebar is None:
                return
            # Find the group that contains the current active item
            current = sidebar.current_item()
            for gi, group in enumerate(sidebar.groups()):
                item_keys = [item.key for item in group.items()]
                if current in item_keys:
                    sidebar.activate_sub_item(gi, sub_index)
                    return
            # Fallback: use first group
            sidebar.activate_sub_item(0, sub_index)

        return _switch

    def _activate_tab(self, target: str) -> None:
        activate_fn = getattr(self._main_window, "_activate_tab", None)
        if callable(activate_fn):
            activate_fn(target)

    def _trigger_backup(self) -> None:
        from app.services.backup_restore import create_quick_backup

        try:
            create_quick_backup()
            self._main_window.show_toast("\u0420\u0435\u0437\u0435\u0440\u0432\u043d\u0430\u044f \u043a\u043e\u043f\u0438\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0430", "info")  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            self._main_window.show_toast("\u041e\u0448\u0438\u0431\u043a\u0430 \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f \u0440\u0435\u0437\u0435\u0440\u0432\u043d\u043e\u0439 \u043a\u043e\u043f\u0438\u0438", "error")  # type: ignore[attr-defined]

    def _trigger_undo(self) -> None:
        from app.services.undo_manager import undo_manager

        result = undo_manager.undo()
        if result is not None:
            toast_fn = getattr(self._main_window, "show_toast", None)
            if callable(toast_fn):
                toast_fn(f"\u041e\u0442\u043c\u0435\u043d\u0435\u043d\u043e: {result}", "info")

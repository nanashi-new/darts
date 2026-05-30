"""Small help button that shows contextual help for a tab."""

from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QPushButton, QWidget

from app.resources.help_context import HELP_CONTEXT


class HelpButton(QPushButton):
    """A '?' button that shows contextual help for the given tab."""

    def __init__(self, tab_name: str, parent: QWidget | None = None) -> None:
        super().__init__("?", parent)
        self._tab_name = tab_name
        self.setObjectName(f"help_btn_{tab_name}")
        self.setFixedSize(24, 24)
        self.setToolTip("Справка по разделу")
        self.clicked.connect(self._show_help)

    def _show_help(self) -> None:
        """Display contextual help in a message box."""
        text = HELP_CONTEXT.get(self._tab_name, "Справка для данного раздела пока недоступна.")
        QMessageBox.information(self, f"Справка: {self._tab_name}", text)

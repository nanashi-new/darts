from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app import __build_info__, __version__


class AboutView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        title = QLabel("Darts Rating EBCK")
        title.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(title)

        version = __version__ or "unknown"
        build = __build_info__ or "unknown"

        for line in (
            f"Версия: {version}",
            f"Сборка: {build}",
            "Локальное приложение для ведения турниров и рейтинга по дартсу.",
        ):
            label = QLabel(line)
            label.setWordWrap(True)
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            layout.addWidget(label)

        layout.addStretch(1)

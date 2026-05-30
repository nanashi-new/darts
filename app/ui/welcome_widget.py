"""Welcome widget shown when the profile has no data."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class WelcomeWidget(QWidget):
    """Displays a welcome message with quick-start tips."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Добро пожаловать в Дартс Лигу!")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 16px;")
        layout.addWidget(title)

        tips = [
            "Добавьте игроков в разделе 'Игроки'",
            "Создайте турнир в разделе 'Турниры'",
            "Импортируйте результаты из Excel в 'Импорт/Экспорт'",
        ]
        tips_text = "\n".join(f"  \u2022  {tip}" for tip in tips)
        tips_label = QLabel(tips_text)
        tips_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tips_label.setStyleSheet("font-size: 15px; line-height: 1.6;")
        tips_label.setWordWrap(True)
        layout.addWidget(tips_label)

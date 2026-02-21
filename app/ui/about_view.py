from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app import __build_info__, __version__


class AboutView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Darts Rating EBCK"))
        layout.addWidget(QLabel(f"Версия: {__version__}"))
        layout.addWidget(QLabel(f"Сборка: {__build_info__}"))
        layout.addWidget(QLabel("Локальное приложение для ведения турниров и рейтинга по дартсу."))
        layout.addStretch(1)

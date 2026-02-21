from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app import __build_info__, __version__


class AboutView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        title_label = QLabel("Darts Rating EBCK", self)
        title_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        layout.addWidget(title_label)

        version_label = QLabel(f"Версия приложения: {__version__}", self)
        layout.addWidget(version_label)

        build_label = QLabel(f"Сборка: {__build_info__}", self)
        layout.addWidget(build_label)

        support_label = QLabel(
            "Поддержка: проект для локальной работы судей и тренеров по дартсу. "
            "Для обратной связи используйте канал сопровождения вашей федерации.",
            self,
        )
        support_label.setWordWrap(True)
        support_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(support_label)

        layout.addStretch(1)

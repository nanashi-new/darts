from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

from app import __build_info__, __build_metadata__, __version__


class AboutView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        scroll_area = QScrollArea(self)
        scroll_area.setObjectName("about_scroll_area")
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        content = QWidget(self)
        scroll_area.setWidget(content)
        content_layout = QVBoxLayout(content)

        labels = [
            "Дартс Лига",
            f"Версия: {__version__}",
            f"Сборка: {__build_info__}",
            f"Время сборки: {__build_metadata__.build_timestamp}",
            f"Git-ревизия: {__build_metadata__.git_revision}",
            f"Версия схемы: {__build_metadata__.schema_version}",
            "Локальное приложение для ведения турниров, рейтинга, импорта и диагностических операций.",
        ]
        for text in labels:
            label = QLabel(text, content)
            label.setWordWrap(True)
            content_layout.addWidget(label)
        content_layout.addStretch(1)

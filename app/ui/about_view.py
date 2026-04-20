from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app import __build_info__, __build_metadata__, __version__


class AboutView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Darts Rating EBCK"))
        layout.addWidget(QLabel(f"Версия: {__version__}"))
        layout.addWidget(QLabel(f"Сборка: {__build_info__}"))
        layout.addWidget(QLabel(f"Build time: {__build_metadata__.build_timestamp}"))
        layout.addWidget(QLabel(f"Git revision: {__build_metadata__.git_revision}"))
        layout.addWidget(QLabel(f"Schema version: {__build_metadata__.schema_version}"))
        layout.addWidget(
            QLabel(
                "Локальное приложение для ведения турниров, рейтинга, импорта и диагностических операций."
            )
        )
        layout.addStretch(1)

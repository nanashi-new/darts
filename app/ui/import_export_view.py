from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ImportExportView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Раздел «Импорт/Экспорт» будет реализован позже."))

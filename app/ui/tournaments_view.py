from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class TournamentsView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Раздел «Турниры» будет реализован позже."))

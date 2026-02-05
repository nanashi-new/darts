from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class RatingView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Раздел «Рейтинг» будет реализован позже."))

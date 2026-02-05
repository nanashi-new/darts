from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class FaqView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Раздел «FAQ» будет реализован позже."))

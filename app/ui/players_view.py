from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PlayersView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Раздел «Игроки» будет реализован позже."))

from pathlib import Path

from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget


def _load_faq_text() -> str:
    faq_path = Path(__file__).resolve().parents[2] / "FAQ.txt"
    try:
        return faq_path.read_text(encoding="utf-8")
    except OSError:
        return "FAQ временно недоступен: не удалось прочитать файл FAQ.txt."


class FaqView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        faq_text = QPlainTextEdit(self)
        faq_text.setReadOnly(True)
        faq_text.setPlainText(_load_faq_text())
        layout.addWidget(faq_text)

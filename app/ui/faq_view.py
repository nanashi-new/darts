from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QLabel, QPlainTextEdit, QVBoxLayout, QWidget


class FaqView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Вопросы и ответы"))

        text = QPlainTextEdit(self)
        text.setReadOnly(True)
        text.setPlainText(self._load_faq_text())
        layout.addWidget(text)

    def _load_faq_text(self) -> str:
        faq_path = Path(__file__).resolve().parents[2] / "FAQ.txt"
        try:
            content = faq_path.read_text(encoding="utf-8").strip()
            if content:
                return content
        except OSError:
            pass
        return "Раздел вопросов и ответов временно недоступен. Проверьте наличие файла FAQ.txt рядом с приложением."

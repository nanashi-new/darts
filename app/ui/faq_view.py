from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QLabel, QTextBrowser, QVBoxLayout, QWidget


class FaqView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Вопросы и ответы", self)
        title.setWordWrap(True)
        layout.addWidget(title)

        guide = QTextBrowser(self)
        guide.setObjectName("faq_guide")
        guide.setReadOnly(True)
        guide.setOpenExternalLinks(False)
        guide.setMarkdown(self._load_faq_text())
        layout.addWidget(guide)

    def _load_faq_text(self) -> str:
        faq_path = Path(__file__).resolve().parents[2] / "FAQ.txt"
        try:
            content = faq_path.read_text(encoding="utf-8").strip()
            if content:
                return content
        except OSError:
            pass
        return (
            "# Вопросы и ответы\n\n"
            "Раздел временно недоступен. Проверьте наличие файла FAQ.txt рядом с приложением."
        )

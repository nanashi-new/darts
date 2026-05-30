"""Help view (formerly FAQ view) with searchable user guide and guided tour launcher."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


class HelpView(QWidget):
    """Full help view with search, user guide content, and tour launcher."""

    tour_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        title = QLabel("Вопросы и ответы", self)
        title.setWordWrap(True)
        layout.addWidget(title)

        self._search_input = QLineEdit(self)
        self._search_input.setObjectName("help_search_input")
        self._search_input.setPlaceholderText("Поиск по руководству...")
        self._search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self._search_input)

        self._guide = QTextBrowser(self)
        self._guide.setObjectName("faq_guide")
        self._guide.setReadOnly(True)
        self._guide.setOpenExternalLinks(False)
        layout.addWidget(self._guide)

        self._tour_btn = QPushButton("Начать обучение", self)
        self._tour_btn.setObjectName("start_tour_btn")
        self._tour_btn.setToolTip("Запустить интерактивный тур по приложению")
        self._tour_btn.clicked.connect(self.tour_requested.emit)
        layout.addWidget(self._tour_btn)

        self._full_content = self._load_guide_text()
        self._guide.setMarkdown(self._full_content)

    def _load_guide_text(self) -> str:
        """Load user guide from resources, falling back to FAQ.txt."""
        guide_path = Path(__file__).resolve().parents[1] / "resources" / "user_guide.md"
        try:
            content = guide_path.read_text(encoding="utf-8").strip()
            if content:
                return content
        except OSError:
            pass
        faq_path = Path(__file__).resolve().parents[2] / "FAQ.txt"
        try:
            content = faq_path.read_text(encoding="utf-8").strip()
            if content:
                return content
        except OSError:
            pass
        return (
            "# Руководство пользователя\n\n"
            "Раздел временно недоступен. Проверьте наличие файла user_guide.md."
        )

    def _on_search_changed(self, text: str) -> None:
        """Filter guide content to show only sections matching the search term."""
        if not text.strip():
            self._guide.setMarkdown(self._full_content)
            return
        filtered = self._filter_sections(text.strip().lower())
        self._guide.setMarkdown(filtered)

    def _filter_sections(self, query: str) -> str:
        """Return only sections whose content contains the query."""
        lines = self._full_content.split("\n")
        sections: list[tuple[str, list[str]]] = []
        current_header = ""
        current_lines: list[str] = []

        for line in lines:
            if line.startswith("## "):
                if current_header or current_lines:
                    sections.append((current_header, current_lines))
                current_header = line
                current_lines = []
            elif line.startswith("# ") and not current_header:
                current_header = line
                current_lines = []
            else:
                current_lines.append(line)

        if current_header or current_lines:
            sections.append((current_header, current_lines))

        result_parts: list[str] = []
        for header, content_lines in sections:
            section_text = (header + "\n" + "\n".join(content_lines)).lower()
            if query in section_text:
                result_parts.append(header)
                result_parts.extend(content_lines)
                result_parts.append("")

        if not result_parts:
            return f"По запросу «{query}» ничего не найдено."
        return "\n".join(result_parts)


# Backward compatibility alias
FaqView = HelpView

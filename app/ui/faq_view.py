from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QLabel, QPlainTextEdit, QVBoxLayout, QWidget

_FALLBACK_FAQ_TEXT = """FAQ — Часто задаваемые вопросы

1) Как добавить игрока?
Раздел «Игроки» → «Добавить» → заполнить данные → «Сохранить».

2) Как импортировать турнир из Excel?
Раздел «Турниры» → «Добавить турнир» → «Импорт XLSX» → выбрать файл → подтвердить → «Пересчитать».

3) Почему у игрока 0 очков за дисциплину?
Разряд по нормативам ЕВСК не выполнен для этой дисциплины.

4) Как изменить количество турниров в рейтинге (N)?
Раздел «Настройки» → «Окно рейтинга» → выбрать значение от 3 до 12.

5) Как распечатать рейтинг?
Раздел «Рейтинг» → «Печать» или «Экспорт PDF»."""


class FaqView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("FAQ"))

        text = QPlainTextEdit(self)
        text.setReadOnly(True)
        text.setPlainText(self._load_faq_text())
        layout.addWidget(text)

    def _candidate_paths(self) -> list[Path]:
        roots: list[Path] = [
            Path(__file__).resolve().parents[2],
            Path.cwd(),
            Path(sys.argv[0]).resolve().parent if sys.argv and sys.argv[0] else Path.cwd(),
        ]
        seen: set[Path] = set()
        paths: list[Path] = []
        for root in roots:
            candidate = root / "FAQ.txt"
            if candidate not in seen:
                seen.add(candidate)
                paths.append(candidate)
        return paths

    def _load_faq_text(self) -> str:
        for faq_path in self._candidate_paths():
            try:
                content = faq_path.read_text(encoding="utf-8-sig").strip()
            except OSError:
                continue
            if content:
                return content
        return _FALLBACK_FAQ_TEXT

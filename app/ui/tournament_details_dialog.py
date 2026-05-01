from __future__ import annotations

import json

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.ui.labels import category_label, league_label, tournament_status_label


class TournamentDetailsDialog(QDialog):
    def __init__(self, *, tournament: dict[str, object], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Детали турнира")
        self.resize(620, 560)

        root_layout = QVBoxLayout(self)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        root_layout.addWidget(scroll_area)

        content = QWidget(self)
        scroll_area.setWidget(content)
        form = QFormLayout(content)

        fields = [
            ("name", "Название", self._value),
            ("date", "Дата", self._value),
            ("status", "Статус", tournament_status_label),
            ("category_code", "Категория", category_label),
            ("league_code", "Лига", league_label),
            ("type", "Тип", self._tournament_type_label),
            ("season", "Сезон", self._value),
            ("series", "Серия", self._value),
            ("location", "Локация", self._value),
            ("organizer", "Организатор", self._value),
            ("source_files", "Файлы источника", self._source_files_label),
            ("has_draft_changes", "Черновые изменения", self._bool_label),
            ("warning_state", "Предупреждения", self._state_label),
            ("error_state", "Ошибки", self._state_label),
            ("confirmed_by", "Подтвердил", self._value),
            ("published_by", "Опубликовал", self._value),
            ("id", "ID турнира", self._value),
        ]
        for key, label, formatter in fields:
            form.addRow(label, self._text(formatter(tournament.get(key))))

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        if close_button := buttons.button(QDialogButtonBox.StandardButton.Close):
            close_button.setText("Закрыть")
        buttons.rejected.connect(self.reject)
        root_layout.addWidget(buttons)

    def _text(self, value: str) -> QLabel:
        label = QLabel(value, self)
        label.setWordWrap(True)
        return label

    def _value(self, value: object) -> str:
        if value in (None, ""):
            return "-"
        return str(value)

    def _bool_label(self, value: object) -> str:
        if value in (None, ""):
            return "-"
        return "да" if bool(value) else "нет"

    def _state_label(self, value: object) -> str:
        if value in (None, "", "none"):
            return "нет"
        return str(value)

    def _tournament_type_label(self, value: object) -> str:
        labels = {
            "standard": "обычный",
            "manual_adult": "взрослый ручной",
        }
        if value in (None, ""):
            return "-"
        return labels.get(str(value), str(value))

    def _source_files_label(self, value: object) -> str:
        if value in (None, ""):
            return "-"
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return value
        else:
            parsed = value
        if isinstance(parsed, list):
            return "\n".join(str(item) for item in parsed) if parsed else "-"
        return str(parsed)

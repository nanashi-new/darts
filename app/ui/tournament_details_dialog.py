from __future__ import annotations

import json

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.ui.labels import (
    category_label,
    league_label,
    tournament_status_color,
    tournament_status_label,
)


class TournamentDetailsDialog(QDialog):
    def __init__(self, *, tournament: dict[str, object], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Детали турнира")
        self.resize(620, 560)

        root_layout = QVBoxLayout(self)

        # Lifecycle stepper
        current_status = str(tournament.get("status") or "draft")
        self._stepper_widget = self._build_stepper(current_status)
        self._stepper_widget.setObjectName("tournament_lifecycle_stepper")
        root_layout.addWidget(self._stepper_widget)

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

    def _build_stepper(self, current_status: str) -> QWidget:
        """Build a visual lifecycle stepper showing progression through stages."""
        steps = [
            ("draft", "\u0427\u0435\u0440\u043D\u043E\u0432\u0438\u043A"),
            ("review", "\u041D\u0430 \u043F\u0440\u043E\u0432\u0435\u0440\u043A\u0435"),
            ("confirmed", "\u041F\u043E\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043D"),
            ("published", "\u041E\u043F\u0443\u0431\u043B\u0438\u043A\u043E\u0432\u0430\u043D"),
        ]
        widget = QWidget(self)
        h_layout = QHBoxLayout(widget)
        h_layout.setContentsMargins(4, 4, 4, 4)

        step_keys = [s[0] for s in steps]
        is_archived = current_status == "archived"
        is_canceled = current_status == "canceled"
        current_index = step_keys.index(current_status) if current_status in step_keys else -1

        for i, (key, label_text) in enumerate(steps):
            if i > 0:
                arrow = QLabel(" \u2192 ", widget)
                arrow.setStyleSheet("color: #9E9E9E;")
                h_layout.addWidget(arrow)

            step_label = QLabel(label_text, widget)
            if is_archived:
                # Archived: all steps shown as completed (green)
                step_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            elif is_canceled:
                # Canceled: all steps shown as grey
                step_label.setStyleSheet("color: #9E9E9E;")
            elif i == current_index:
                color = tournament_status_color(key)
                step_label.setStyleSheet(f"font-weight: bold; color: {color};")
            elif i < current_index:
                step_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            else:
                step_label.setStyleSheet("color: #9E9E9E;")
            h_layout.addWidget(step_label)

        # Add terminal status label for archived/canceled
        if is_archived:
            arrow = QLabel(" \u2192 ", widget)
            arrow.setStyleSheet("color: #9E9E9E;")
            h_layout.addWidget(arrow)
            terminal_label = QLabel("\u0412 \u0430\u0440\u0445\u0438\u0432\u0435", widget)
            terminal_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            h_layout.addWidget(terminal_label)
        elif is_canceled:
            arrow = QLabel(" \u2192 ", widget)
            arrow.setStyleSheet("color: #9E9E9E;")
            h_layout.addWidget(arrow)
            terminal_label = QLabel("\u041E\u0442\u043C\u0435\u043D\u0435\u043D", widget)
            terminal_label.setStyleSheet("color: #F44336; font-weight: bold;")
            h_layout.addWidget(terminal_label)

        h_layout.addStretch(1)
        return widget

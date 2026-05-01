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

from app.services.notes import NoteRecord
from app.services.training_journal import TrainingEntryRecord
from app.ui.labels import (
    entity_type_label,
    note_type_label,
    priority_label,
    session_type_label,
    visibility_label,
)


class ContextNoteDetailsDialog(QDialog):
    def __init__(self, *, note: NoteRecord, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Детали заметки")
        self.resize(620, 520)

        form = self._build_form()
        fields = [
            ("Объект", note.entity_label or f"{entity_type_label(note.entity_type)}: {note.entity_id}"),
            ("Тип", note_type_label(note.note_type)),
            ("Доступ", visibility_label(note.visibility)),
            ("Приоритет", priority_label(note.priority)),
            ("Закреплена", "да" if note.is_pinned else "нет"),
            ("Архив", "да" if note.is_archived else "нет"),
            ("Автор", note.author or "-"),
            ("Заголовок", note.title),
            ("Текст", note.body),
            ("Создано", note.created_at.replace("T", " ")[:19]),
            ("Обновлено", note.updated_at.replace("T", " ")[:19]),
            ("ID заметки", str(note.id)),
        ]
        for label, value in fields:
            form.addRow(label, self._text(value))

        self._add_close_button()

    def _build_form(self) -> QFormLayout:
        root_layout = QVBoxLayout(self)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        root_layout.addWidget(scroll_area)
        content = QWidget(self)
        scroll_area.setWidget(content)
        self._root_layout = root_layout
        return QFormLayout(content)

    def _add_close_button(self) -> None:
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        if close_button := buttons.button(QDialogButtonBox.StandardButton.Close):
            close_button.setText("Закрыть")
        buttons.rejected.connect(self.reject)
        self._root_layout.addWidget(buttons)

    def _text(self, value: str) -> QLabel:
        label = QLabel(value or "-", self)
        label.setWordWrap(True)
        return label


class ContextTrainingDetailsDialog(QDialog):
    def __init__(self, *, entry: TrainingEntryRecord, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Детали тренировки")
        self.resize(620, 560)

        form = self._build_form()
        fields = [
            ("Игрок", entry.player_fio),
            ("Дата", entry.training_date),
            ("Тренер", entry.coach_name or "-"),
            ("Тип", session_type_label(entry.session_type)),
            ("Итоги", entry.summary),
            ("Цели", entry.goals or "-"),
            ("Метрики", self._metrics_label(entry.metrics)),
            ("Турнир", entry.tournament_name or "-"),
            ("Следующее действие", entry.next_action or "-"),
            ("Архив", "да" if entry.is_archived else "нет"),
            ("Создано", entry.created_at.replace("T", " ")[:19]),
            ("Обновлено", entry.updated_at.replace("T", " ")[:19]),
            ("ID записи", str(entry.id)),
        ]
        for label, value in fields:
            form.addRow(label, self._text(value))

        self._add_close_button()

    def _build_form(self) -> QFormLayout:
        root_layout = QVBoxLayout(self)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        root_layout.addWidget(scroll_area)
        content = QWidget(self)
        scroll_area.setWidget(content)
        self._root_layout = root_layout
        return QFormLayout(content)

    def _add_close_button(self) -> None:
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        if close_button := buttons.button(QDialogButtonBox.StandardButton.Close):
            close_button.setText("Закрыть")
        buttons.rejected.connect(self.reject)
        self._root_layout.addWidget(buttons)

    def _text(self, value: str) -> QLabel:
        label = QLabel(value or "-", self)
        label.setWordWrap(True)
        return label

    def _metrics_label(self, metrics: dict[str, object]) -> str:
        if not metrics:
            return "-"
        return json.dumps(metrics, ensure_ascii=False, sort_keys=True)

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from app.services.notes import EntityNoteDefaults, create_note, list_entity_notes


@dataclass(frozen=True)
class EntityNoteFormData:
    title: str
    body: str
    note_type: str
    visibility: str
    priority: str
    author: str | None
    is_pinned: bool


NOTE_TYPE_OPTIONS: list[tuple[str, str]] = [
    ("Player note", "player_note"),
    ("Coach note", "coach_note"),
    ("Follow-up", "follow_up"),
    ("Tournament note", "tournament_note"),
    ("League note", "league_note"),
]

VISIBILITY_OPTIONS: list[tuple[str, str]] = [
    ("Personal", "personal"),
    ("Internal service", "internal_service"),
    ("Coach-only", "coach_only"),
    ("Follow-up", "follow_up"),
]

PRIORITY_OPTIONS: list[tuple[str, str]] = [
    ("Low", "low"),
    ("Normal", "normal"),
    ("High", "high"),
]


class EntityNoteDialog(QDialog):
    def __init__(self, *, defaults: EntityNoteDefaults | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Новая note")
        self.resize(520, 420)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.title_input = QLineEdit(self)
        self.author_input = QLineEdit(self)
        self.type_combo = QComboBox(self)
        self.visibility_combo = QComboBox(self)
        self.priority_combo = QComboBox(self)
        self.body_input = QTextEdit(self)
        self.body_input.setMinimumHeight(140)
        self.is_pinned_checkbox = QCheckBox("Pinned", self)

        for label, value in NOTE_TYPE_OPTIONS:
            self.type_combo.addItem(label, value)
        for label, value in VISIBILITY_OPTIONS:
            self.visibility_combo.addItem(label, value)
        for label, value in PRIORITY_OPTIONS:
            self.priority_combo.addItem(label, value)

        form.addRow("Title*", self.title_input)
        form.addRow("Author", self.author_input)
        form.addRow("Type", self.type_combo)
        form.addRow("Visibility", self.visibility_combo)
        form.addRow("Priority", self.priority_combo)
        form.addRow("Body*", self.body_input)
        form.addRow("", self.is_pinned_checkbox)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.accepted.connect(self._accept_if_valid)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._apply_defaults(defaults)

    def _apply_defaults(self, defaults: EntityNoteDefaults | None) -> None:
        if defaults is None:
            return
        if defaults.author:
            self.author_input.setText(defaults.author)
        self.is_pinned_checkbox.setChecked(defaults.is_pinned)
        self._set_combo_value(self.type_combo, defaults.note_type)
        self._set_combo_value(self.visibility_combo, defaults.visibility)
        self._set_combo_value(self.priority_combo, defaults.priority)

    def _accept_if_valid(self) -> None:
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Note", "Title is required.")
            return
        if not self.body_input.toPlainText().strip():
            QMessageBox.warning(self, "Note", "Body is required.")
            return
        self.accept()

    def form_data(self) -> EntityNoteFormData:
        author = self.author_input.text().strip() or None
        return EntityNoteFormData(
            title=self.title_input.text().strip(),
            body=self.body_input.toPlainText().strip(),
            note_type=str(self.type_combo.currentData()),
            visibility=str(self.visibility_combo.currentData()),
            priority=str(self.priority_combo.currentData()),
            author=author,
            is_pinned=self.is_pinned_checkbox.isChecked(),
        )

    @staticmethod
    def _set_combo_value(combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)


class EntityNotesDialog(QDialog):
    def __init__(
        self,
        *,
        connection: sqlite3.Connection,
        entity_type: str,
        entity_id: str,
        defaults: EntityNoteDefaults | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._connection = connection
        self._entity_type = entity_type
        self._entity_id = entity_id
        self._defaults = defaults

        self.setWindowTitle(f"Notes: {entity_type}:{entity_id}")
        self.resize(860, 520)

        layout = QVBoxLayout(self)
        layout.addWidget(self._build_filters_group())
        layout.addWidget(self._build_notes_table())
        layout.addLayout(self._build_actions())

        self._refresh_notes()

    def _build_filters_group(self) -> QGroupBox:
        group = QGroupBox("Filters", self)
        layout = QHBoxLayout(group)

        self.search_input = QLineEdit(group)
        self.search_input.setPlaceholderText("Search in title/body")
        self.search_input.textChanged.connect(self._refresh_notes)

        self.note_type_filter_combo = QComboBox(group)
        self.note_type_filter_combo.addItem("All types", None)
        for label, value in NOTE_TYPE_OPTIONS:
            self.note_type_filter_combo.addItem(label, value)
        self.note_type_filter_combo.currentIndexChanged.connect(self._refresh_notes)

        self.visibility_filter_combo = QComboBox(group)
        self.visibility_filter_combo.addItem("All visibilities", None)
        for label, value in VISIBILITY_OPTIONS:
            self.visibility_filter_combo.addItem(label, value)
        self.visibility_filter_combo.currentIndexChanged.connect(self._refresh_notes)

        layout.addWidget(self.search_input)
        layout.addWidget(self.note_type_filter_combo)
        layout.addWidget(self.visibility_filter_combo)
        return group

    def _build_notes_table(self) -> QTableWidget:
        self.notes_table = QTableWidget(0, 7, self)
        self.notes_table.setHorizontalHeaderLabels(
            ["Title", "Type", "Visibility", "Priority", "Pinned", "Author", "Created"]
        )
        self.notes_table.verticalHeader().setVisible(False)
        self.notes_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.notes_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        return self.notes_table

    def _build_actions(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        self.add_note_button = QPushButton("Добавить note", self)
        self.add_note_button.clicked.connect(self._open_create_dialog)
        layout.addWidget(self.add_note_button)
        layout.addStretch(1)
        return layout

    def _refresh_notes(self) -> None:
        note_type = self.note_type_filter_combo.currentData()
        visibility = self.visibility_filter_combo.currentData()
        notes = list_entity_notes(
            connection=self._connection,
            entity_type=self._entity_type,
            entity_id=self._entity_id,
            note_types=[str(note_type)] if note_type else None,
            visibilities=[str(visibility)] if visibility else None,
            query=self.search_input.text().strip() or None,
        )
        self.notes_table.setRowCount(0)
        for note in notes:
            row_index = self.notes_table.rowCount()
            self.notes_table.insertRow(row_index)
            values = [
                note.title,
                note.note_type,
                note.visibility,
                note.priority,
                "yes" if note.is_pinned else "",
                note.author or "",
                str(note.created_at).replace("T", " ")[:19],
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column in {4, 6}:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.notes_table.setItem(row_index, column, item)

    def _open_create_dialog(self) -> None:
        dialog = EntityNoteDialog(defaults=self._defaults, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        form_data = dialog.form_data()
        create_note(
            connection=self._connection,
            entity_type=self._entity_type,
            entity_id=self._entity_id,
            note_type=form_data.note_type,
            visibility=form_data.visibility,
            title=form_data.title,
            body=form_data.body,
            priority=form_data.priority,
            author=form_data.author,
            is_pinned=form_data.is_pinned,
        )
        self._refresh_notes()

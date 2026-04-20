from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.db.database import get_connection
from app.services.notes import list_notes_hub
from app.services.training_journal import list_training_entries
from app.ui.player_card_dialog import PlayerCardDialog
from app.ui_state import get_view_state, update_view_state


class ContextView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._connection = get_connection()
        layout = QVBoxLayout(self)

        tabs = QTabWidget(self)
        tabs.addTab(self._build_notes_tab(), "Notes")
        tabs.addTab(self._build_training_tab(), "Training")
        layout.addWidget(tabs)
        self._tabs = tabs

        self._restore_state()
        self._refresh_notes()
        self._refresh_training()
        tabs.currentChanged.connect(self._persist_state)

    def _build_notes_tab(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        filters = QHBoxLayout()
        self.notes_search_input = QLineEdit(widget)
        self.notes_search_input.setPlaceholderText("Search notes")
        self.notes_search_input.textChanged.connect(self._on_notes_filters_changed)
        self.notes_entity_filter = QComboBox(widget)
        self.notes_entity_filter.addItem("All entities", None)
        self.notes_entity_filter.addItem("Players", "player")
        self.notes_entity_filter.addItem("Tournaments", "tournament")
        self.notes_entity_filter.addItem("Leagues", "league")
        self.notes_entity_filter.currentIndexChanged.connect(self._on_notes_filters_changed)
        self.notes_type_filter = QComboBox(widget)
        self.notes_type_filter.addItem("All note types", None)
        for value in ["player_note", "coach_note", "follow_up", "tournament_note", "league_note"]:
            self.notes_type_filter.addItem(value, value)
        self.notes_type_filter.currentIndexChanged.connect(self._on_notes_filters_changed)
        self.notes_visibility_filter = QComboBox(widget)
        self.notes_visibility_filter.addItem("All visibilities", None)
        for value in ["personal", "internal_service", "coach_only", "follow_up"]:
            self.notes_visibility_filter.addItem(value, value)
        self.notes_visibility_filter.currentIndexChanged.connect(self._on_notes_filters_changed)
        self.coach_only_checkbox = QCheckBox("Coach-only", widget)
        self.coach_only_checkbox.toggled.connect(self._on_notes_filters_changed)
        filters.addWidget(self.notes_search_input)
        filters.addWidget(self.notes_entity_filter)
        filters.addWidget(self.notes_type_filter)
        filters.addWidget(self.notes_visibility_filter)
        filters.addWidget(self.coach_only_checkbox)
        layout.addLayout(filters)

        self.notes_table = QTableWidget(0, 7, widget)
        self.notes_table.setHorizontalHeaderLabels(
            ["Entity", "Title", "Type", "Visibility", "Priority", "Author", "Created"]
        )
        layout.addWidget(self.notes_table)

        actions = QHBoxLayout()
        self.open_related_note_entity_button = QPushButton("Open related entity", widget)
        self.open_related_note_entity_button.clicked.connect(self._open_selected_note_entity)
        actions.addWidget(self.open_related_note_entity_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        return widget

    def _build_training_tab(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        filters = QHBoxLayout()
        self.training_search_input = QLineEdit(widget)
        self.training_search_input.setPlaceholderText("Search training")
        self.training_search_input.textChanged.connect(self._on_training_filters_changed)
        filters.addWidget(self.training_search_input)
        layout.addLayout(filters)

        self.training_table = QTableWidget(0, 6, widget)
        self.training_table.setHorizontalHeaderLabels(
            ["Player", "Date", "Coach", "Type", "Summary", "Next action"]
        )
        layout.addWidget(self.training_table)

        actions = QHBoxLayout()
        self.open_training_player_button = QPushButton("Open player card", widget)
        self.open_training_player_button.clicked.connect(self._open_selected_training_player)
        actions.addWidget(self.open_training_player_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        return widget

    def _restore_state(self) -> None:
        state = get_view_state("context")
        self.notes_search_input.blockSignals(True)
        self.notes_search_input.setText(str(state.get("notes_search") or ""))
        self.notes_search_input.blockSignals(False)
        self._select_combo_value(self.notes_entity_filter, state.get("notes_entity_type"))
        self._select_combo_value(self.notes_type_filter, state.get("notes_type"))
        self._select_combo_value(self.notes_visibility_filter, state.get("notes_visibility"))
        self.coach_only_checkbox.blockSignals(True)
        self.coach_only_checkbox.setChecked(bool(state.get("coach_only")))
        self.coach_only_checkbox.blockSignals(False)
        self.training_search_input.blockSignals(True)
        self.training_search_input.setText(str(state.get("training_search") or ""))
        self.training_search_input.blockSignals(False)

        target_tab = state.get("current_tab")
        if isinstance(target_tab, str):
            for index in range(self._tabs.count()):
                if self._tabs.tabText(index) == target_tab:
                    self._tabs.setCurrentIndex(index)
                    break

    def _persist_state(self, *_args) -> None:
        update_view_state(
            "context",
            {
                "current_tab": self._tabs.tabText(self._tabs.currentIndex()),
                "notes_search": self.notes_search_input.text(),
                "notes_entity_type": self.notes_entity_filter.currentData(),
                "notes_type": self.notes_type_filter.currentData(),
                "notes_visibility": self.notes_visibility_filter.currentData(),
                "coach_only": self.coach_only_checkbox.isChecked(),
                "training_search": self.training_search_input.text(),
            },
        )

    def _on_notes_filters_changed(self, *_args) -> None:
        self._persist_state()
        self._refresh_notes()

    def _on_training_filters_changed(self, *_args) -> None:
        self._persist_state()
        self._refresh_training()

    def _refresh_notes(self) -> None:
        entity_type = self.notes_entity_filter.currentData()
        note_type = self.notes_type_filter.currentData()
        visibility = self.notes_visibility_filter.currentData()
        visibilities = [str(visibility)] if visibility else None
        if self.coach_only_checkbox.isChecked():
            visibilities = ["coach_only"]
        notes = list_notes_hub(
            connection=self._connection,
            entity_types=[str(entity_type)] if entity_type else None,
            note_types=[str(note_type)] if note_type else None,
            visibilities=visibilities,
            query=self.notes_search_input.text().strip() or None,
        )
        self.notes_table.setRowCount(0)
        for note in notes:
            row_index = self.notes_table.rowCount()
            self.notes_table.insertRow(row_index)
            values = [
                note.entity_label or f"{note.entity_type}:{note.entity_id}",
                note.title,
                note.note_type,
                note.visibility,
                note.priority,
                note.author or "",
                str(note.created_at).replace("T", " ")[:19],
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column == 6:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setData(Qt.ItemDataRole.UserRole, note.entity_type)
                item.setData(Qt.ItemDataRole.UserRole + 1, note.entity_id)
                self.notes_table.setItem(row_index, column, item)

    def _refresh_training(self) -> None:
        entries = list_training_entries(
            connection=self._connection,
            query=self.training_search_input.text().strip() or None,
        )
        self.training_table.setRowCount(0)
        for entry in entries:
            row_index = self.training_table.rowCount()
            self.training_table.insertRow(row_index)
            values = [
                entry.player_fio,
                entry.training_date,
                entry.coach_name or "",
                entry.session_type,
                entry.summary,
                entry.next_action or "",
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.ItemDataRole.UserRole, entry.player_id)
                self.training_table.setItem(row_index, column, item)

    def _open_selected_note_entity(self) -> None:
        row = self.notes_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Context", "Select a note row first.")
            return
        item = self.notes_table.item(row, 0)
        if item is None:
            return
        entity_type = str(item.data(Qt.ItemDataRole.UserRole) or "")
        entity_id = str(item.data(Qt.ItemDataRole.UserRole + 1) or "")
        if entity_type == "player" and entity_id.isdigit():
            PlayerCardDialog(connection=self._connection, player_id=int(entity_id), parent=self).exec()
            return
        QMessageBox.information(self, "Context", f"Open entity is not implemented for {entity_type}:{entity_id}.")

    def _open_selected_training_player(self) -> None:
        row = self.training_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Context", "Select a training row first.")
            return
        item = self.training_table.item(row, 0)
        if item is None:
            return
        player_id = item.data(Qt.ItemDataRole.UserRole)
        if player_id is None:
            return
        PlayerCardDialog(connection=self._connection, player_id=int(player_id), parent=self).exec()

    @staticmethod
    def _select_combo_value(combo: QComboBox, value: object) -> None:
        combo.blockSignals(True)
        for index in range(combo.count()):
            if combo.itemData(index) == value:
                combo.setCurrentIndex(index)
                break
        combo.blockSignals(False)

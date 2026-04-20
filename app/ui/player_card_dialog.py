from __future__ import annotations

import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.db.repositories import PlayerRepository, ResultRepository
from app.services.league_transfer import LeagueTransferEvent, list_player_league_transfers
from app.services.notes import EntityNoteDefaults, NoteRecord, create_note, list_entity_notes
from app.services.rating_snapshot import PlayerRatingStateEntry, list_latest_player_rating_states
from app.services.training_journal import TrainingEntryRecord, create_training_entry, list_player_training_entries
from app.ui.entity_notes_dialog import EntityNoteDialog, EntityNotesDialog
from app.ui.rating_history_dialog import RatingHistoryDialog
from app.ui.training_entry_dialog import TrainingEntryDialog


class PlayerCardDialog(QDialog):
    def __init__(self, *, connection: sqlite3.Connection, player_id: int, parent=None) -> None:
        super().__init__(parent)
        self._connection = connection
        self._player_id = player_id
        self._player_repo = PlayerRepository(connection)
        self._result_repo = ResultRepository(connection)
        self._rating_states: list[PlayerRatingStateEntry] = []

        player = self._player_repo.get(player_id)
        if player is None:
            raise ValueError("Player was not found.")
        self._player = player
        self.setWindowTitle(f"Карточка игрока: {self._build_fio(player)}")
        self.resize(980, 760)

        layout = QVBoxLayout(self)
        layout.addWidget(self._build_overview_group())
        layout.addWidget(self._build_notes_group())
        layout.addWidget(self._build_training_group())
        layout.addWidget(self._build_rating_group())
        layout.addWidget(self._build_tournament_history_group())
        layout.addWidget(self._build_league_history_group())

        self._load_context()

    def _build_overview_group(self) -> QGroupBox:
        group = QGroupBox("Overview", self)
        layout = QVBoxLayout(group)
        self.overview_label = QLabel(group)
        self.overview_label.setWordWrap(True)
        layout.addWidget(self.overview_label)
        return group

    def _build_notes_group(self) -> QGroupBox:
        group = QGroupBox("Notes", self)
        layout = QVBoxLayout(group)
        controls = QHBoxLayout()
        self.add_note_button = QPushButton("Добавить note", group)
        self.coach_note_button = QPushButton("Coach note", group)
        self.all_notes_button = QPushButton("Все notes", group)
        self.add_note_button.clicked.connect(self._add_note)
        self.coach_note_button.clicked.connect(self._add_coach_note)
        self.all_notes_button.clicked.connect(self._open_all_notes)
        controls.addWidget(self.add_note_button)
        controls.addWidget(self.coach_note_button)
        controls.addWidget(self.all_notes_button)
        controls.addStretch(1)
        layout.addLayout(controls)

        self.notes_table = QTableWidget(0, 5, group)
        self.notes_table.setHorizontalHeaderLabels(["Title", "Type", "Visibility", "Priority", "Created"])
        self.notes_table.verticalHeader().setVisible(False)
        self.notes_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.notes_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        layout.addWidget(self.notes_table)
        return group

    def _build_rating_group(self) -> QGroupBox:
        group = QGroupBox("Rating states", self)
        layout = QVBoxLayout(group)
        controls = QHBoxLayout()
        self.open_rating_history_button = QPushButton("Открыть историю рейтинга", group)
        self.open_rating_history_button.clicked.connect(self._open_selected_rating_history)
        controls.addWidget(self.open_rating_history_button)
        controls.addStretch(1)
        layout.addLayout(controls)

        self.rating_state_table = QTableWidget(0, 5, group)
        self.rating_state_table.setHorizontalHeaderLabels(
            ["Scope type", "Scope key", "Место", "Очки", "Учтено турниров"]
        )
        self.rating_state_table.verticalHeader().setVisible(False)
        self.rating_state_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.rating_state_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.rating_state_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.rating_state_table.itemSelectionChanged.connect(self._refresh_rating_history_button_state)
        layout.addWidget(self.rating_state_table)
        return group

    def _build_training_group(self) -> QGroupBox:
        group = QGroupBox("Training journal", self)
        layout = QVBoxLayout(group)
        controls = QHBoxLayout()
        self.add_training_button = QPushButton("Add training", group)
        self.add_training_button.clicked.connect(self._add_training_entry)
        controls.addWidget(self.add_training_button)
        controls.addStretch(1)
        layout.addLayout(controls)

        self.training_table = QTableWidget(0, 5, group)
        self.training_table.setHorizontalHeaderLabels(
            ["Date", "Coach", "Type", "Summary", "Next action"]
        )
        self.training_table.verticalHeader().setVisible(False)
        self.training_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.training_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        layout.addWidget(self.training_table)
        return group

    def _build_tournament_history_group(self) -> QGroupBox:
        group = QGroupBox("Tournament history", self)
        layout = QVBoxLayout(group)
        self.tournament_history_table = QTableWidget(0, 5, group)
        self.tournament_history_table.setHorizontalHeaderLabels(
            ["Дата турнира", "Турнир", "Категория", "Место", "Итого"]
        )
        self.tournament_history_table.verticalHeader().setVisible(False)
        self.tournament_history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tournament_history_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        layout.addWidget(self.tournament_history_table)
        return group

    def _build_league_history_group(self) -> QGroupBox:
        group = QGroupBox("League history", self)
        layout = QVBoxLayout(group)
        self.league_history_table = QTableWidget(0, 4, group)
        self.league_history_table.setHorizontalHeaderLabels(["Дата", "Из лиги", "В лигу", "Турнир"])
        self.league_history_table.verticalHeader().setVisible(False)
        self.league_history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.league_history_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        layout.addWidget(self.league_history_table)
        return group

    def _load_context(self) -> None:
        self.overview_label.setText(self._build_overview_text())
        self._fill_tournament_history(self._result_repo.list_player_history(self._player_id))
        self._reload_notes()
        self._fill_training_entries(
            list_player_training_entries(connection=self._connection, player_id=self._player_id)
        )
        self._fill_league_history(list_player_league_transfers(self._connection, self._player_id))
        self._rating_states = list_latest_player_rating_states(self._connection, player_id=self._player_id)
        self._fill_rating_states(self._rating_states)
        self._refresh_rating_history_button_state()

    def _build_overview_text(self) -> str:
        player = self._player
        return "\n".join(
            [
                f"ФИО: {self._build_fio(player)}",
                f"Дата рождения: {player.get('birth_date') or '—'}",
                f"Пол: {player.get('gender') or '—'}",
                f"Клуб: {player.get('club') or '—'}",
                f"Тренер: {player.get('coach') or '—'}",
                f"Примечания: {player.get('notes') or '—'}",
            ]
        )

    def _fill_tournament_history(self, rows: list[dict[str, object]]) -> None:
        self.tournament_history_table.setRowCount(0)
        for row_data in rows:
            row_index = self.tournament_history_table.rowCount()
            self.tournament_history_table.insertRow(row_index)
            self._set_table_row(
                self.tournament_history_table,
                row_index,
                [
                    row_data.get("tournament_date"),
                    row_data.get("tournament_name"),
                    row_data.get("category_code"),
                    row_data.get("place"),
                    row_data.get("points_total"),
                ],
            )

    def _fill_notes(self, rows: list[NoteRecord]) -> None:
        self.notes_table.setRowCount(0)
        for row_data in rows:
            row_index = self.notes_table.rowCount()
            self.notes_table.insertRow(row_index)
            self._set_table_row(
                self.notes_table,
                row_index,
                [
                    row_data.title,
                    row_data.note_type,
                    row_data.visibility,
                    row_data.priority,
                    str(row_data.created_at).replace("T", " ")[:19],
                ],
            )

    def _fill_training_entries(self, rows: list[TrainingEntryRecord]) -> None:
        self.training_table.setRowCount(0)
        for row_data in rows:
            row_index = self.training_table.rowCount()
            self.training_table.insertRow(row_index)
            self._set_table_row(
                self.training_table,
                row_index,
                [
                    row_data.training_date,
                    row_data.coach_name or "",
                    row_data.session_type,
                    row_data.summary,
                    row_data.next_action or "",
                ],
            )

    def _fill_league_history(self, rows: list[LeagueTransferEvent]) -> None:
        self.league_history_table.setRowCount(0)
        for row_data in rows:
            row_index = self.league_history_table.rowCount()
            self.league_history_table.insertRow(row_index)
            self._set_table_row(
                self.league_history_table,
                row_index,
                [
                    str(row_data.created_at).replace("T", " ")[:19],
                    row_data.from_league_code or "",
                    row_data.to_league_code,
                    row_data.tournament_name,
                ],
            )

    def _fill_rating_states(self, rows: list[PlayerRatingStateEntry]) -> None:
        self.rating_state_table.setRowCount(0)
        for row_data in rows:
            row_index = self.rating_state_table.rowCount()
            self.rating_state_table.insertRow(row_index)
            self._set_table_row(
                self.rating_state_table,
                row_index,
                [
                    row_data.scope_type,
                    row_data.scope_key,
                    row_data.position,
                    row_data.points,
                    row_data.tournaments_count,
                ],
            )
        if rows:
            self.rating_state_table.selectRow(0)

    def _refresh_rating_history_button_state(self) -> None:
        row = self.rating_state_table.currentRow()
        self.open_rating_history_button.setEnabled(0 <= row < len(self._rating_states))

    def _open_selected_rating_history(self) -> None:
        row = self.rating_state_table.currentRow()
        if row < 0 or row >= len(self._rating_states):
            return
        rating_state = self._rating_states[row]
        dialog = RatingHistoryDialog(
            connection=self._connection,
            scope_type=rating_state.scope_type,
            scope_key=rating_state.scope_key,
            parent=self,
        )
        dialog.exec()

    def _add_note(self) -> None:
        self._open_note_dialog(
            EntityNoteDefaults(
                note_type="player_note",
                visibility="internal_service",
            )
        )

    def _add_coach_note(self) -> None:
        self._open_note_dialog(
            EntityNoteDefaults(
                note_type="coach_note",
                visibility="coach_only",
            )
        )

    def _open_note_dialog(self, defaults: EntityNoteDefaults) -> None:
        dialog = EntityNoteDialog(defaults=defaults, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        form_data = dialog.form_data()
        create_note(
            connection=self._connection,
            entity_type="player",
            entity_id=str(self._player_id),
            note_type=form_data.note_type,
            visibility=form_data.visibility,
            title=form_data.title,
            body=form_data.body,
            priority=form_data.priority,
            author=form_data.author,
            is_pinned=form_data.is_pinned,
        )
        self._reload_notes()

    def _open_all_notes(self) -> None:
        dialog = EntityNotesDialog(
            connection=self._connection,
            entity_type="player",
            entity_id=str(self._player_id),
            defaults=EntityNoteDefaults(
                note_type="player_note",
                visibility="internal_service",
            ),
            parent=self,
        )
        dialog.exec()
        self._reload_notes()

    def _reload_notes(self) -> None:
        self._fill_notes(
            list_entity_notes(
                connection=self._connection,
                entity_type="player",
                entity_id=str(self._player_id),
            )
        )

    def _add_training_entry(self) -> None:
        dialog = TrainingEntryDialog(
            default_coach_name=str(self._player.get("coach") or "").strip() or None,
            parent=self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        form_data = dialog.form_data()
        create_training_entry(
            connection=self._connection,
            player_id=self._player_id,
            coach_name=form_data.coach_name,
            training_date=form_data.training_date,
            session_type=form_data.session_type,
            summary=form_data.summary,
            goals=form_data.goals,
            metrics=form_data.metrics,
            related_tournament_id=None,
            next_action=form_data.next_action,
        )
        self._fill_training_entries(
            list_player_training_entries(connection=self._connection, player_id=self._player_id)
        )

    @staticmethod
    def _set_table_row(table: QTableWidget, row_index: int, values: list[object]) -> None:
        for column, value in enumerate(values):
            item = QTableWidgetItem("" if value is None else str(value))
            if column not in {1, 3}:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row_index, column, item)

    @staticmethod
    def _build_fio(player: dict[str, object]) -> str:
        return " ".join(
            part
            for part in [
                str(player.get("last_name") or "").strip(),
                str(player.get("first_name") or "").strip(),
                str(player.get("middle_name") or "").strip(),
            ]
            if part
        )

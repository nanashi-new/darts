from __future__ import annotations

import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.db.repositories import PlayerRepository, ResultRepository
from app.services.league_transfer import LeagueTransferEvent, list_player_league_transfers
from app.services.notes import EntityNoteDefaults, NoteRecord, create_note, list_entity_notes
from app.services.rating_snapshot import PlayerRatingStateEntry, list_latest_player_rating_states
from app.services.training_journal import TrainingEntryRecord, create_training_entry, list_player_training_entries
from app.ui.attachments_widget import AttachmentsWidget
from app.ui.custom_fields_widget import CustomFieldsWidget
from app.ui.entity_notes_dialog import EntityNoteDialog, EntityNotesDialog
from app.ui.labels import (
    adult_scope_label,
    category_label,
    gender_label,
    league_label,
    note_type_label,
    priority_label,
    scope_type_label,
    session_type_label,
    visibility_label,
)
from app.ui.rating_history_dialog import RatingHistoryDialog
from app.ui.tags_widget import TagsWidget
from app.ui.training_entry_dialog import TrainingEntryDialog


class PlayerCardDialog(QDialog):
    def __init__(self, *, connection: sqlite3.Connection, player_id: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._connection = connection
        self._player_id = player_id
        self._player_repo = PlayerRepository(connection)
        self._result_repo = ResultRepository(connection)
        self._rating_states: list[PlayerRatingStateEntry] = []
        self._all_notes: list[NoteRecord] = []
        self._league_transfers: list[LeagueTransferEvent] = []
        self._tournament_history: list[dict[str, object]] = []

        player = self._player_repo.get(player_id)
        if player is None:
            raise ValueError("Игрок не найден.")
        self._player = player
        self.setWindowTitle(f"Карточка игрока: {self._build_fio(player)}")
        self.resize(980, 760)

        root_layout = QVBoxLayout(self)

        # Keep content_scroll for backward compatibility
        self.content_scroll = QScrollArea(self)
        self.content_scroll.setWidgetResizable(True)

        self._tab_widget = QTabWidget(self)
        self.content_scroll.setWidget(self._tab_widget)
        root_layout.addWidget(self.content_scroll)

        # Build tabs
        self._tab_widget.addTab(self._build_general_tab(), "Общее")
        self._tab_widget.addTab(self._build_rating_tab(), "Рейтинг")
        self._tab_widget.addTab(self._build_tournaments_tab(), "Турниры")
        self._tab_widget.addTab(self._build_notes_tab(), "Заметки")
        self._tab_widget.addTab(self._build_training_tab(), "Тренировки")
        self._tab_widget.addTab(self._build_history_tab(), "История")

        self._load_context()

    # ─── Tab 1: General ─────────────────────────────────────────

    def _build_general_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)

        # Overview
        overview_group = QGroupBox("Обзор", container)
        overview_layout = QVBoxLayout(overview_group)
        self.overview_label = QLabel(overview_group)
        self.overview_label.setWordWrap(True)
        overview_layout.addWidget(self.overview_label)
        layout.addWidget(overview_group)

        # Current league
        league_group = QGroupBox("Текущая лига", container)
        league_layout = QVBoxLayout(league_group)
        self.current_league_label = QLabel("", league_group)
        league_layout.addWidget(self.current_league_label)
        layout.addWidget(league_group)

        # Current rating position
        rating_pos_group = QGroupBox("Позиция в рейтинге", container)
        rating_pos_layout = QVBoxLayout(rating_pos_group)
        self.current_rating_position_label = QLabel("", rating_pos_group)
        rating_pos_layout.addWidget(self.current_rating_position_label)
        layout.addWidget(rating_pos_group)

        # Tags widget
        tags_group = QGroupBox("Теги", container)
        tags_layout = QVBoxLayout(tags_group)
        self.tags_widget = TagsWidget(
            connection=self._connection,
            entity_type="player",
            entity_id=str(self._player_id),
            parent=tags_group,
        )
        tags_layout.addWidget(self.tags_widget)
        layout.addWidget(tags_group)

        # Custom fields widget
        custom_fields_group = QGroupBox("Кастомные поля", container)
        custom_fields_layout = QVBoxLayout(custom_fields_group)
        self.custom_fields_widget = CustomFieldsWidget(
            connection=self._connection,
            player_id=self._player_id,
            parent=custom_fields_group,
        )
        custom_fields_layout.addWidget(self.custom_fields_widget)
        layout.addWidget(custom_fields_group)

        layout.addStretch(1)
        scroll.setWidget(container)
        return scroll

    # ─── Tab 2: Rating ──────────────────────────────────────────

    def _build_rating_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)

        # Trend label
        self.rating_trend_label = QLabel("Динамика: ...", container)
        layout.addWidget(self.rating_trend_label)

        # Rating controls
        controls = QHBoxLayout()
        self.open_rating_history_button = QPushButton("Открыть историю рейтинга", container)
        self.open_rating_history_button.clicked.connect(self._open_selected_rating_history)
        controls.addWidget(self.open_rating_history_button)
        controls.addStretch(1)
        layout.addLayout(controls)

        # Rating table
        self.rating_state_table = QTableWidget(0, 5, container)
        self.rating_state_table.setHorizontalHeaderLabels(
            ["Раздел", "Значение", "Место", "Очки", "Учтено турниров"]
        )
        self.rating_state_table.verticalHeader().setVisible(False)
        self.rating_state_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.rating_state_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.rating_state_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.rating_state_table.itemSelectionChanged.connect(self._refresh_rating_history_button_state)
        layout.addWidget(self.rating_state_table)

        layout.addStretch(1)
        scroll.setWidget(container)
        return scroll

    # ─── Tab 3: Tournaments ─────────────────────────────────────

    def _build_tournaments_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)

        # Summary label
        self.tournament_summary_label = QLabel("Всего турниров: 0 | Лучшее место: - | Средние очки: -", container)
        layout.addWidget(self.tournament_summary_label)

        # Tournament table
        self.tournament_history_table = QTableWidget(0, 5, container)
        self.tournament_history_table.setHorizontalHeaderLabels(
            ["Дата турнира", "Турнир", "Категория", "Место", "Итого"]
        )
        self.tournament_history_table.verticalHeader().setVisible(False)
        self.tournament_history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tournament_history_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        layout.addWidget(self.tournament_history_table)

        layout.addStretch(1)
        scroll.setWidget(container)
        return scroll

    # ─── Tab 4: Notes ───────────────────────────────────────────

    def _build_notes_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)

        # Filter
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Фильтр:", container)
        filter_layout.addWidget(filter_label)
        self.notes_filter_combo = QComboBox(container)
        self.notes_filter_combo.addItems(["Все", "Заметка игрока", "Заметка тренера", "Контрольное действие"])
        self.notes_filter_combo.currentIndexChanged.connect(self._apply_notes_filter)
        filter_layout.addWidget(self.notes_filter_combo)
        filter_layout.addStretch(1)
        layout.addLayout(filter_layout)

        # Buttons
        controls = QHBoxLayout()
        self.add_note_button = QPushButton("Добавить заметку", container)
        self.coach_note_button = QPushButton("Заметка тренера", container)
        self.all_notes_button = QPushButton("Все заметки", container)
        self.add_note_button.clicked.connect(self._add_note)
        self.coach_note_button.clicked.connect(self._add_coach_note)
        self.all_notes_button.clicked.connect(self._open_all_notes)
        controls.addWidget(self.add_note_button)
        controls.addWidget(self.coach_note_button)
        controls.addWidget(self.all_notes_button)
        controls.addStretch(1)
        layout.addLayout(controls)

        # Notes table
        self.notes_table = QTableWidget(0, 5, container)
        self.notes_table.setHorizontalHeaderLabels(["Заголовок", "Тип", "Доступ", "Приоритет", "Создано"])
        self.notes_table.verticalHeader().setVisible(False)
        self.notes_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.notes_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        layout.addWidget(self.notes_table)

        layout.addStretch(1)
        scroll.setWidget(container)
        return scroll

    # ─── Tab 5: Training ────────────────────────────────────────

    def _build_training_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)

        # Summary label
        self.training_summary_label = QLabel("Всего тренировок: 0 | Последняя: -", container)
        layout.addWidget(self.training_summary_label)

        # Button
        controls = QHBoxLayout()
        self.add_training_button = QPushButton("Добавить тренировку", container)
        self.add_training_button.clicked.connect(self._add_training_entry)
        controls.addWidget(self.add_training_button)
        controls.addStretch(1)
        layout.addLayout(controls)

        # Training table
        self.training_table = QTableWidget(0, 5, container)
        self.training_table.setHorizontalHeaderLabels(
            ["Дата", "Тренер", "Тип", "Итоги", "Следующее действие"]
        )
        self.training_table.verticalHeader().setVisible(False)
        self.training_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.training_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        layout.addWidget(self.training_table)

        layout.addStretch(1)
        scroll.setWidget(container)
        return scroll

    # ─── Tab 6: History ─────────────────────────────────────────

    def _build_history_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)

        # League history table
        self.league_history_table = QTableWidget(0, 4, container)
        self.league_history_table.setHorizontalHeaderLabels(["Дата", "Из лиги", "В лигу", "Турнир"])
        self.league_history_table.verticalHeader().setVisible(False)
        self.league_history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.league_history_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        layout.addWidget(self.league_history_table)

        # Attachments widget
        attachments_group = QGroupBox("Вложения", container)
        attachments_layout = QVBoxLayout(attachments_group)
        self.attachments_widget = AttachmentsWidget(
            connection=self._connection,
            entity_type="player",
            entity_id=str(self._player_id),
            parent=attachments_group,
        )
        attachments_layout.addWidget(self.attachments_widget)
        layout.addWidget(attachments_group)

        layout.addStretch(1)
        scroll.setWidget(container)
        return scroll

    # ─── Data loading ───────────────────────────────────────────

    def _load_context(self) -> None:
        self.overview_label.setText(self._build_overview_text())

        # Tournament history
        self._tournament_history = self._result_repo.list_player_history(self._player_id)
        self._fill_tournament_history(self._tournament_history)
        self._update_tournament_summary()

        # Notes
        self._reload_notes()

        # Training
        training_entries = list_player_training_entries(connection=self._connection, player_id=self._player_id)
        self._fill_training_entries(training_entries)
        self._update_training_summary(training_entries)

        # League transfers
        self._league_transfers = list_player_league_transfers(self._connection, self._player_id)
        self._fill_league_history(self._league_transfers)
        self._update_current_league()

        # Rating states
        self._rating_states = list_latest_player_rating_states(self._connection, player_id=self._player_id)
        self._fill_rating_states(self._rating_states)
        self._refresh_rating_history_button_state()
        self._update_rating_trend()
        self._update_current_rating_position()

    def _build_overview_text(self) -> str:
        player = self._player
        return "\n".join(
            [
                f"ФИО: {self._build_fio(player)}",
                f"Дата рождения: {player.get('birth_date') or '—'}",
                f"Пол: {gender_label(player.get('gender')) if player.get('gender') else '—'}",
                f"Клуб: {player.get('club') or '—'}",
                f"Тренер: {player.get('coach') or '—'}",
                f"Примечания: {player.get('notes') or '—'}",
            ]
        )

    def _update_current_league(self) -> None:
        if self._league_transfers:
            latest = self._league_transfers[0]
            self.current_league_label.setText(league_label(latest.to_league_code))
        else:
            self.current_league_label.setText("Нет данных")

    def _update_current_rating_position(self) -> None:
        if self._rating_states:
            first = self._rating_states[0]
            self.current_rating_position_label.setText(f"Место: {first.position}")
        else:
            self.current_rating_position_label.setText("Нет данных")

    def _update_rating_trend(self) -> None:
        if not self._rating_states:
            self.rating_trend_label.setText("Динамика: нет данных")
            return
        # Compare first (current/best) position vs last (oldest) position
        # Lower position number is better
        current = self._rating_states[0]
        oldest = self._rating_states[-1]
        if current.position < oldest.position:
            trend = "рост"
        elif current.position > oldest.position:
            trend = "снижение"
        else:
            trend = "стабильно"
        self.rating_trend_label.setText(f"Динамика: {trend}")

    def _update_tournament_summary(self) -> None:
        rows = self._tournament_history
        count = len(rows)
        if count == 0:
            self.tournament_summary_label.setText("Всего турниров: 0 | Лучшее место: - | Средние очки: -")
            return
        places = [int(r["place"]) for r in rows if r.get("place") is not None]  # type: ignore[arg-type]
        points = [float(r["points_total"]) for r in rows if r.get("points_total") is not None]  # type: ignore[arg-type]
        best_place = min(places) if places else "-"
        avg_points = round(sum(points) / len(points), 1) if points else "-"
        self.tournament_summary_label.setText(
            f"Всего турниров: {count} | Лучшее место: {best_place} | Средние очки: {avg_points}"
        )

    def _update_training_summary(self, entries: list[TrainingEntryRecord]) -> None:
        count = len(entries)
        if count == 0:
            self.training_summary_label.setText("Всего тренировок: 0 | Последняя: -")
            return
        last_date = entries[0].training_date
        self.training_summary_label.setText(f"Всего тренировок: {count} | Последняя: {last_date}")

    # ─── Notes filtering ────────────────────────────────────────

    def _apply_notes_filter(self) -> None:
        filter_text = self.notes_filter_combo.currentText()
        if filter_text == "Все":
            self._fill_notes(self._all_notes)
        else:
            # Map display label back to note_type code
            type_map = {
                "Заметка игрока": "player_note",
                "Заметка тренера": "coach_note",
                "Контрольное действие": "follow_up",
            }
            code = type_map.get(filter_text, "")
            filtered = [n for n in self._all_notes if n.note_type == code]
            self._fill_notes(filtered)

    # ─── Table fill methods ─────────────────────────────────────

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
                    category_label(row_data.get("category_code")),
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
                    note_type_label(row_data.note_type),
                    visibility_label(row_data.visibility),
                    priority_label(row_data.priority),
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
                    session_type_label(row_data.session_type),
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
                    league_label(row_data.from_league_code) if row_data.from_league_code else "",
                    league_label(row_data.to_league_code),
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
                    scope_type_label(row_data.scope_type),
                    self._rating_scope_key_label(row_data),
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

    @staticmethod
    def _rating_scope_key_label(row_data: PlayerRatingStateEntry) -> str:
        if row_data.scope_type == "adult":
            return adult_scope_label(row_data.scope_key)
        if row_data.scope_type == "category":
            return category_label(row_data.scope_key)
        if row_data.scope_type == "league":
            return league_label(row_data.scope_key)
        return row_data.scope_key

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

    # ─── Note actions ───────────────────────────────────────────

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
        self._all_notes = list_entity_notes(
            connection=self._connection,
            entity_type="player",
            entity_id=str(self._player_id),
        )
        self._apply_notes_filter()

    # ─── Training actions ───────────────────────────────────────

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
        entries = list_player_training_entries(connection=self._connection, player_id=self._player_id)
        self._fill_training_entries(entries)
        self._update_training_summary(entries)

    # ─── Utility ────────────────────────────────────────────────

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

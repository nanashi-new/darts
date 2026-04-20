from __future__ import annotations

import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from app.db.database import get_connection
from app.db.repositories import PlayerRepository, ResultRepository
from app.services.audit_log import AuditLogService, ERROR
from app.services.league_transfer import list_player_league_transfers
from app.ui.player_card_dialog import PlayerCardDialog
from app.ui.player_edit_dialog import PlayerEditDialog
from app.ui_state import get_view_state, update_view_state

PLAYER_CREATE = "PLAYER_CREATE"
PLAYER_UPDATE = "PLAYER_UPDATE"
PLAYER_DELETE = "PLAYER_DELETE"


class PlayersView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._connection = get_connection()
        self._player_repo = PlayerRepository(self._connection)
        self._result_repo = ResultRepository(self._connection)
        self._audit_log_service = AuditLogService(self._connection)
        self._players: list[dict[str, object]] = []

        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Поиск:"))
        self._search_input = QLineEdit(self)
        self._search_input.setPlaceholderText("Фамилия, имя или отчество")
        self._search_input.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self._search_input)

        self._card_btn = QPushButton("Карточка", self)
        add_btn = QPushButton("Добавить", self)
        edit_btn = QPushButton("Редактировать", self)
        delete_btn = QPushButton("Удалить", self)

        self._card_btn.clicked.connect(self._open_player_card)
        add_btn.clicked.connect(self._add_player)
        edit_btn.clicked.connect(self._edit_selected_player)
        delete_btn.clicked.connect(self._delete_selected_player)

        toolbar.addWidget(self._card_btn)
        toolbar.addWidget(add_btn)
        toolbar.addWidget(edit_btn)
        toolbar.addWidget(delete_btn)
        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Vertical, self)

        self._players_table = QTableView(self)
        self._players_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._players_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._players_table.setSortingEnabled(False)
        self._players_table.doubleClicked.connect(lambda *_args: self._open_player_card())
        splitter.addWidget(self._players_table)

        history_container = QWidget(self)
        history_layout = QVBoxLayout(history_container)
        self._history_title = QLabel("История игрока", self)
        self._history_table = QTableView(self)
        self._history_table.setSortingEnabled(False)
        self._league_history_title = QLabel("История лиг", self)
        self._league_history_table = QTableView(self)
        self._league_history_table.setSortingEnabled(False)
        history_layout.addWidget(self._history_title)
        history_layout.addWidget(self._history_table)
        history_layout.addWidget(self._league_history_title)
        history_layout.addWidget(self._league_history_table)
        splitter.addWidget(history_container)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

        self._restore_state()
        self._refresh_players()

    def _restore_state(self) -> None:
        state = get_view_state("players")
        search = state.get("search")
        if isinstance(search, str):
            self._search_input.blockSignals(True)
            self._search_input.setText(search)
            self._search_input.blockSignals(False)

    def _on_search_changed(self, text: str) -> None:
        update_view_state("players", {"search": text})
        self._refresh_players()

    def _refresh_players(self) -> None:
        query = self._search_input.text().strip().lower()
        players = self._player_repo.list()
        if query:
            self._players = [
                player
                for player in players
                if query in " ".join(
                    part.lower()
                    for part in [
                        str(player.get("last_name") or ""),
                        str(player.get("first_name") or ""),
                        str(player.get("middle_name") or ""),
                    ]
                    if part
                )
            ]
        else:
            self._players = players

        model = QStandardItemModel(self)
        columns = [
            ("id", "ID"),
            ("last_name", "Фамилия"),
            ("first_name", "Имя"),
            ("middle_name", "Отчество"),
            ("birth_date", "Дата рождения"),
            ("gender", "Пол"),
            ("club", "Клуб"),
            ("coach", "Тренер"),
        ]
        model.setColumnCount(len(columns))
        model.setHorizontalHeaderLabels([label for _, label in columns])

        for player in self._players:
            row_items: list[QStandardItem] = []
            for key, _ in columns:
                display = "" if player.get(key) is None else str(player.get(key))
                item = QStandardItem(display)
                item.setEditable(False)
                if key == "id":
                    item.setTextAlignment(Qt.AlignCenter)
                row_items.append(item)
            model.appendRow(row_items)

        self._players_table.setModel(model)
        self._players_table.resizeColumnsToContents()
        selection_model = self._players_table.selectionModel()
        if selection_model is not None:
            selection_model.selectionChanged.connect(self._on_player_selected)

        self._card_btn.setEnabled(model.rowCount() > 0)
        if model.rowCount() > 0:
            self._players_table.selectRow(0)
        else:
            self._set_history([])
            self._set_league_history([])
            self._history_title.setText("История игрока")
            self._league_history_title.setText("История лиг")

    def _selected_player(self) -> dict[str, object] | None:
        selection_model = self._players_table.selectionModel()
        if selection_model is None:
            return None
        indexes = selection_model.selectedRows()
        if not indexes:
            return None
        row = indexes[0].row()
        if row < 0 or row >= len(self._players):
            return None
        return self._players[row]

    def _on_player_selected(self, *_args) -> None:
        player = self._selected_player()
        self._card_btn.setEnabled(player is not None)
        if player is None:
            self._set_history([])
            self._set_league_history([])
            self._history_title.setText("История игрока")
            self._league_history_title.setText("История лиг")
            return

        player_id = int(player["id"])
        fio = self._build_fio(player)
        history = self._result_repo.list_player_history(player_id)
        league_history = list_player_league_transfers(self._connection, player_id)
        self._history_title.setText(f"История игрока: {fio} (записей: {len(history)})")
        self._league_history_title.setText(f"История лиг: {fio} (записей: {len(league_history)})")
        self._set_history(history)
        self._set_league_history(league_history)

    def _set_history(self, history_rows: list[dict[str, object]]) -> None:
        columns = [
            ("tournament_date", "Дата турнира"),
            ("tournament_name", "Турнир"),
            ("category_code", "Категория"),
            ("place", "Место"),
            ("points_total", "Итого"),
        ]
        model = QStandardItemModel(self)
        model.setColumnCount(len(columns))
        model.setHorizontalHeaderLabels([label for _, label in columns])

        for row_data in history_rows:
            row_items = []
            for key, _ in columns:
                value = row_data.get(key)
                item = QStandardItem("" if value is None else str(value))
                item.setEditable(False)
                row_items.append(item)
            model.appendRow(row_items)

        self._history_table.setModel(model)
        self._history_table.resizeColumnsToContents()

    def _set_league_history(self, history_rows: list[object]) -> None:
        columns = [
            ("created_at", "Дата"),
            ("from_league_code", "Из лиги"),
            ("to_league_code", "В лигу"),
            ("tournament_name", "Турнир"),
        ]
        model = QStandardItemModel(self)
        model.setColumnCount(len(columns))
        model.setHorizontalHeaderLabels([label for _, label in columns])

        for row_data in history_rows:
            row_items = []
            for key, _ in columns:
                value = getattr(row_data, key, None)
                if key == "created_at" and value:
                    value = str(value).replace("T", " ")[:19]
                item = QStandardItem("" if value is None else str(value))
                item.setEditable(False)
                row_items.append(item)
            model.appendRow(row_items)

        self._league_history_table.setModel(model)
        self._league_history_table.resizeColumnsToContents()

    def _open_player_card(self) -> None:
        player = self._selected_player()
        if player is None:
            QMessageBox.information(self, "Игроки", "Выберите игрока для открытия карточки.")
            return
        dialog = PlayerCardDialog(
            connection=self._connection,
            player_id=int(player["id"]),
            parent=self,
        )
        dialog.exec()

    def _add_player(self) -> None:
        dialog = PlayerEditDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.form_data()
        payload = {
            "last_name": data.last_name,
            "first_name": data.first_name,
            "middle_name": data.middle_name,
            "birth_date": data.birth_date,
            "gender": data.gender,
            "coach": data.coach,
            "club": data.club,
            "notes": data.notes,
        }
        try:
            player_id = self._player_repo.create(payload)
        except sqlite3.Error as exc:
            self._audit_log_service.log_event(ERROR, "Ошибка создания игрока", str(exc), level="error")
            QMessageBox.critical(self, "Игроки", "Не удалось создать игрока.")
            return

        self._audit_log_service.log_event(
            PLAYER_CREATE,
            "Создан игрок",
            f"ID: {player_id}; ФИО: {data.last_name} {data.first_name}",
            context={"player_id": player_id},
        )
        self._refresh_players()

    def _edit_selected_player(self) -> None:
        player = self._selected_player()
        if player is None:
            QMessageBox.information(self, "Игроки", "Выберите игрока для редактирования.")
            return

        dialog = PlayerEditDialog(self, player=player)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.form_data()
        payload = {
            "last_name": data.last_name,
            "first_name": data.first_name,
            "middle_name": data.middle_name,
            "birth_date": data.birth_date,
            "gender": data.gender,
            "coach": data.coach,
            "club": data.club,
            "notes": data.notes,
        }
        player_id = int(player["id"])

        try:
            self._player_repo.update(player_id, payload)
        except sqlite3.Error as exc:
            self._audit_log_service.log_event(ERROR, "Ошибка обновления игрока", str(exc), level="error")
            QMessageBox.critical(self, "Игроки", "Не удалось обновить данные игрока.")
            return

        self._audit_log_service.log_event(
            PLAYER_UPDATE,
            "Обновлён игрок",
            f"ID: {player_id}; ФИО: {data.last_name} {data.first_name}",
            context={"player_id": player_id},
        )
        self._refresh_players()

    def _delete_selected_player(self) -> None:
        player = self._selected_player()
        if player is None:
            QMessageBox.information(self, "Игроки", "Выберите игрока для удаления.")
            return

        player_id = int(player["id"])
        fio = self._build_fio(player)
        confirm = QMessageBox.question(
            self,
            "Удаление игрока",
            (
                f"Удалить игрока '{fio}' (ID: {player_id})?\n"
                "Связанные результаты турниров также будут удалены."
            ),
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            self._player_repo.delete(player_id)
        except sqlite3.Error as exc:
            self._audit_log_service.log_event(ERROR, "Ошибка удаления игрока", str(exc), level="error")
            QMessageBox.critical(self, "Игроки", "Не удалось удалить игрока.")
            return

        self._audit_log_service.log_event(
            PLAYER_DELETE,
            "Удалён игрок",
            f"ID: {player_id}; ФИО: {fio}",
            context={"player_id": player_id},
        )
        self._refresh_players()

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

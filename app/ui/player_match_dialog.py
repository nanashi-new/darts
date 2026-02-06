from __future__ import annotations

from typing import Iterable

from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPushButton,
    QTableView,
    QVBoxLayout,
)


class PlayerMatchDialog(QDialog):
    def __init__(
        self,
        *,
        fio: str,
        birth_date_or_year: str | None,
        candidates: Iterable[dict[str, object]],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Выбор игрока")
        self.resize(860, 420)

        self._candidates = list(candidates)
        self._action: str = "cancel"
        self._selected_player_id: int | None = None

        layout = QVBoxLayout(self)
        birth_caption = birth_date_or_year or "—"
        layout.addWidget(QLabel(f"Найдено несколько игроков для: {fio} (ДР/год: {birth_caption})", self))

        self.table_view = QTableView(self)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table_view.setSortingEnabled(False)
        self._fill_table()
        layout.addWidget(self.table_view)

        self.remember_checkbox = QCheckBox("Запомнить выбор для этого ФИО+ДР", self)
        layout.addWidget(self.remember_checkbox)

        button_box = QDialogButtonBox(self)
        self.select_button = QPushButton("Выбрать", self)
        self.create_button = QPushButton("Создать нового", self)
        self.cancel_button = QPushButton("Отмена импорта", self)
        button_box.addButton(self.select_button, QDialogButtonBox.ButtonRole.AcceptRole)
        button_box.addButton(self.create_button, QDialogButtonBox.ButtonRole.ActionRole)
        button_box.addButton(self.cancel_button, QDialogButtonBox.ButtonRole.RejectRole)
        layout.addWidget(button_box)

        self.select_button.clicked.connect(self._on_select)
        self.create_button.clicked.connect(self._on_create_new)
        self.cancel_button.clicked.connect(self._on_cancel)

        if self._candidates:
            self.table_view.selectRow(0)

    def resolution(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "action": self._action,
            "remember": bool(self.remember_checkbox.isChecked()),
        }
        if self._selected_player_id is not None:
            payload["player_id"] = self._selected_player_id
        return payload

    def _fill_table(self) -> None:
        model = QStandardItemModel(self)
        model.setColumnCount(4)
        model.setHorizontalHeaderLabels(["ФИО", "ДР", "Клуб", "Тренер"])

        for player in self._candidates:
            fio = " ".join(
                part
                for part in (
                    player.get("last_name"),
                    player.get("first_name"),
                    player.get("middle_name"),
                )
                if part
            )
            birth_date = str(player.get("birth_date") or "")
            club = str(player.get("club") or "")
            coach = str(player.get("coach") or "")
            row = [QStandardItem(fio), QStandardItem(birth_date), QStandardItem(club), QStandardItem(coach)]
            for item in row:
                item.setEditable(False)
            model.appendRow(row)

        self.table_view.setModel(model)
        self.table_view.resizeColumnsToContents()

    def _selected_candidate(self) -> dict[str, object] | None:
        indexes = self.table_view.selectionModel().selectedRows()
        if not indexes:
            return None
        row = indexes[0].row()
        if row < 0 or row >= len(self._candidates):
            return None
        return self._candidates[row]

    def _on_select(self) -> None:
        candidate = self._selected_candidate()
        if candidate is None:
            return
        self._selected_player_id = int(candidate["id"])
        self._action = "select"
        self.accept()

    def _on_create_new(self) -> None:
        self._selected_player_id = None
        self._action = "create"
        self.accept()

    def _on_cancel(self) -> None:
        self._selected_player_id = None
        self._action = "cancel"
        self.reject()

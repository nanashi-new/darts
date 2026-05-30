from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.db.repositories import PlayerRepository
from app.services.coach_tasks import CoachTaskRecord


@dataclass(frozen=True)
class CoachTaskFormData:
    title: str
    description: str | None
    player_id: int | None
    due_date: str | None
    priority: str
    category: str | None
    status: str


class CoachTaskDialog(QDialog):
    def __init__(
        self,
        *,
        connection: object,
        edit_record: CoachTaskRecord | None = None,
        default_player_id: int | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._edit_record = edit_record
        self._player_map: dict[int, str] = {}

        if edit_record:
            self.setWindowTitle("Редактирование задачи тренера")
        else:
            self.setWindowTitle("Новая задача тренера")
        self.resize(520, 420)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.title_input = QLineEdit(self)
        self.title_input.setPlaceholderText("Название задачи (обязательно)")

        self.description_input = QTextEdit(self)
        self.description_input.setMinimumHeight(80)

        self.player_combo = QComboBox(self)
        self.player_combo.addItem("-- Без игрока --", None)
        self._load_players(connection)

        self.due_date_checkbox = QCheckBox("Указать срок", self)
        self.due_date_checkbox.setChecked(False)
        self.due_date_checkbox.toggled.connect(self._on_due_date_toggled)

        self.due_date_edit = QDateEdit(self)
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDate(QDate.currentDate())
        self.due_date_edit.setEnabled(False)

        self.priority_combo = QComboBox(self)
        self.priority_combo.addItem("Низкий", "low")
        self.priority_combo.addItem("Обычный", "normal")
        self.priority_combo.addItem("Высокий", "high")
        self.priority_combo.addItem("Срочный", "urgent")
        self.priority_combo.setCurrentIndex(1)

        self.category_input = QLineEdit(self)
        self.category_input.setPlaceholderText("Категория (необязательно)")

        self.status_combo = QComboBox(self)
        self.status_combo.addItem("Открыта", "open")
        self.status_combo.addItem("В работе", "in_progress")
        self.status_combo.addItem("Выполнена", "done")
        self.status_combo.addItem("Отменена", "cancelled")

        form.addRow("Название*", self.title_input)
        form.addRow("Описание", self.description_input)
        form.addRow("Игрок", self.player_combo)
        form.addRow("", self.due_date_checkbox)
        form.addRow("Срок", self.due_date_edit)
        form.addRow("Приоритет", self.priority_combo)
        form.addRow("Категория", self.category_input)
        form.addRow("Статус", self.status_combo)

        if not edit_record:
            self.status_combo.setVisible(False)
            # Hide label too - find it in form layout
            label_item = form.labelForField(self.status_combo)
            if label_item:
                label_item.setVisible(False)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        if save_button := buttons.button(QDialogButtonBox.StandardButton.Save):
            save_button.setText("Сохранить")
        if cancel_button := buttons.button(QDialogButtonBox.StandardButton.Cancel):
            cancel_button.setText("Отмена")
        buttons.accepted.connect(self._accept_if_valid)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Populate fields if editing
        if edit_record:
            self._populate_from_record(edit_record)
        elif default_player_id is not None:
            self._select_player(default_player_id)

    def _load_players(self, connection: object) -> None:
        try:
            import sqlite3
            if isinstance(connection, sqlite3.Connection):
                repo = PlayerRepository(connection)
                players = repo.list()
                for p in players:
                    fio = " ".join(
                        part
                        for part in [
                            str(p.get("last_name") or "").strip(),
                            str(p.get("first_name") or "").strip(),
                            str(p.get("middle_name") or "").strip(),
                        ]
                        if part
                    )
                    player_id = int(p["id"])
                    self._player_map[player_id] = fio
                    self.player_combo.addItem(fio, player_id)
        except Exception:  # noqa: BLE001
            pass

    def _select_player(self, player_id: int) -> None:
        for i in range(self.player_combo.count()):
            if self.player_combo.itemData(i) == player_id:
                self.player_combo.setCurrentIndex(i)
                break

    def _on_due_date_toggled(self, checked: bool) -> None:
        self.due_date_edit.setEnabled(checked)

    def _populate_from_record(self, record: CoachTaskRecord) -> None:
        self.title_input.setText(record.title)
        if record.description:
            self.description_input.setPlainText(record.description)
        if record.player_id is not None:
            self._select_player(record.player_id)
        if record.due_date:
            self.due_date_checkbox.setChecked(True)
            date = QDate.fromString(record.due_date, "yyyy-MM-dd")
            if date.isValid():
                self.due_date_edit.setDate(date)
        else:
            self.due_date_checkbox.setChecked(False)
        # Priority
        for i in range(self.priority_combo.count()):
            if self.priority_combo.itemData(i) == record.priority:
                self.priority_combo.setCurrentIndex(i)
                break
        # Category
        if record.category:
            self.category_input.setText(record.category)
        # Status
        for i in range(self.status_combo.count()):
            if self.status_combo.itemData(i) == record.status:
                self.status_combo.setCurrentIndex(i)
                break

    def _accept_if_valid(self) -> None:
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Задача тренера", "Укажите название задачи.")
            return
        self.accept()

    def form_data(self) -> CoachTaskFormData:
        due_date_val: str | None = None
        if self.due_date_checkbox.isChecked():
            due_date_val = self.due_date_edit.date().toString("yyyy-MM-dd")
        player_id = self.player_combo.currentData()
        return CoachTaskFormData(
            title=self.title_input.text().strip(),
            description=self.description_input.toPlainText().strip() or None,
            player_id=int(player_id) if player_id is not None else None,
            due_date=due_date_val,
            priority=str(self.priority_combo.currentData()),
            category=self.category_input.text().strip() or None,
            status=str(self.status_combo.currentData()),
        )

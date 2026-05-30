from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
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
from app.services.training_plans import TrainingPlanRecord


@dataclass(frozen=True)
class TrainingPlanFormData:
    title: str
    player_id: int
    description: str | None
    goal: str | None
    start_date: str | None
    end_date: str | None
    status: str
    exercises: list[Any]


class TrainingPlanDialog(QDialog):
    def __init__(
        self,
        *,
        connection: object,
        edit_record: TrainingPlanRecord | None = None,
        default_player_id: int | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._edit_record = edit_record
        self._player_map: dict[int, str] = {}

        if edit_record:
            self.setWindowTitle("Редактирование плана тренировок")
        else:
            self.setWindowTitle("Новый план тренировок")
        self.resize(560, 520)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.title_input = QLineEdit(self)
        self.title_input.setPlaceholderText("Название плана (обязательно)")

        self.player_combo = QComboBox(self)
        self._load_players(connection)

        self.description_input = QTextEdit(self)
        self.description_input.setMinimumHeight(70)

        self.goal_input = QTextEdit(self)
        self.goal_input.setMinimumHeight(70)

        self.start_date_edit = QDateEdit(self)
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())

        self.end_date_edit = QDateEdit(self)
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate().addMonths(1))

        self.status_combo = QComboBox(self)
        self.status_combo.addItem("Активный", "active")
        self.status_combo.addItem("Завершен", "completed")
        self.status_combo.addItem("На паузе", "paused")

        self.exercises_input = QTextEdit(self)
        self.exercises_input.setMinimumHeight(90)
        self.exercises_input.setPlaceholderText('[{"name": "...", "reps": 10}]')

        form.addRow("Название*", self.title_input)
        form.addRow("Игрок*", self.player_combo)
        form.addRow("Описание", self.description_input)
        form.addRow("Цель", self.goal_input)
        form.addRow("Дата начала", self.start_date_edit)
        form.addRow("Дата окончания", self.end_date_edit)
        form.addRow("Статус", self.status_combo)
        form.addRow("Упражнения JSON", self.exercises_input)

        if not edit_record:
            self.status_combo.setVisible(False)
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

    def _populate_from_record(self, record: TrainingPlanRecord) -> None:
        self.title_input.setText(record.title)
        self._select_player(record.player_id)
        if record.description:
            self.description_input.setPlainText(record.description)
        if record.goal:
            self.goal_input.setPlainText(record.goal)
        if record.start_date:
            date = QDate.fromString(record.start_date, "yyyy-MM-dd")
            if date.isValid():
                self.start_date_edit.setDate(date)
        if record.end_date:
            date = QDate.fromString(record.end_date, "yyyy-MM-dd")
            if date.isValid():
                self.end_date_edit.setDate(date)
        # Status
        for i in range(self.status_combo.count()):
            if self.status_combo.itemData(i) == record.status:
                self.status_combo.setCurrentIndex(i)
                break
        # Exercises
        if record.exercises:
            self.exercises_input.setPlainText(
                json.dumps(record.exercises, ensure_ascii=False, indent=2)
            )

    def _accept_if_valid(self) -> None:
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "План тренировок", "Укажите название плана.")
            return
        if self.player_combo.count() == 0 or self.player_combo.currentData() is None:
            QMessageBox.warning(self, "План тренировок", "Выберите игрока.")
            return
        exercises_text = self.exercises_input.toPlainText().strip()
        if exercises_text:
            try:
                parsed = json.loads(exercises_text)
            except json.JSONDecodeError:
                QMessageBox.warning(
                    self, "План тренировок", "Упражнения должны быть корректным JSON."
                )
                return
            if not isinstance(parsed, list):
                QMessageBox.warning(
                    self, "План тренировок", "Упражнения JSON должны быть массивом."
                )
                return
        self.accept()

    def form_data(self) -> TrainingPlanFormData:
        exercises_text = self.exercises_input.toPlainText().strip()
        exercises: list[Any] = []
        if exercises_text:
            exercises = json.loads(exercises_text)

        return TrainingPlanFormData(
            title=self.title_input.text().strip(),
            player_id=int(self.player_combo.currentData()),
            description=self.description_input.toPlainText().strip() or None,
            goal=self.goal_input.toPlainText().strip() or None,
            start_date=self.start_date_edit.date().toString("yyyy-MM-dd"),
            end_date=self.end_date_edit.date().toString("yyyy-MM-dd"),
            status=str(self.status_combo.currentData()),
            exercises=exercises,
        )

from __future__ import annotations

import json
from dataclasses import dataclass

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
)


@dataclass(frozen=True)
class TrainingEntryFormData:
    coach_name: str | None
    training_date: str
    session_type: str
    summary: str
    goals: str | None
    metrics: dict[str, object]
    next_action: str | None


class TrainingEntryDialog(QDialog):
    def __init__(self, *, default_coach_name: str | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Новая запись тренировки")
        self.resize(520, 460)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.coach_name_input = QLineEdit(self)
        self.coach_name_input.setText(default_coach_name or "")
        self.training_date_edit = QDateEdit(self)
        self.training_date_edit.setCalendarPopup(True)
        self.training_date_edit.setDate(QDate.currentDate())
        self.session_type_input = QLineEdit(self)
        self.session_type_input.setPlaceholderText("Например: техника, матч, общая")
        self.summary_input = QLineEdit(self)
        self.goals_input = QTextEdit(self)
        self.goals_input.setMinimumHeight(90)
        self.metrics_input = QTextEdit(self)
        self.metrics_input.setPlaceholderText('{"doubles_hit": 10}')
        self.metrics_input.setMinimumHeight(80)
        self.next_action_input = QTextEdit(self)
        self.next_action_input.setMinimumHeight(80)

        form.addRow("Тренер", self.coach_name_input)
        form.addRow("Дата", self.training_date_edit)
        form.addRow("Тип занятия", self.session_type_input)
        form.addRow("Итоги*", self.summary_input)
        form.addRow("Цели", self.goals_input)
        form.addRow("Метрики JSON", self.metrics_input)
        form.addRow("Следующее действие", self.next_action_input)
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

    def _accept_if_valid(self) -> None:
        if not self.summary_input.text().strip():
            QMessageBox.warning(self, "Тренировка", "Заполните краткие итоги тренировки.")
            return
        metrics_text = self.metrics_input.toPlainText().strip()
        if metrics_text:
            try:
                metrics = json.loads(metrics_text)
            except json.JSONDecodeError:
                QMessageBox.warning(self, "Тренировка", "Метрики должны быть корректным JSON.")
                return
            if not isinstance(metrics, dict):
                QMessageBox.warning(self, "Тренировка", "Метрики JSON должны быть объектом.")
                return
        self.accept()

    def form_data(self) -> TrainingEntryFormData:
        metrics_text = self.metrics_input.toPlainText().strip()
        metrics = json.loads(metrics_text) if metrics_text else {}
        return TrainingEntryFormData(
            coach_name=self.coach_name_input.text().strip() or None,
            training_date=self.training_date_edit.date().toString("yyyy-MM-dd"),
            session_type=self.session_type_input.text().strip() or "general",
            summary=self.summary_input.text().strip(),
            goals=self.goals_input.toPlainText().strip() or None,
            metrics=metrics,
            next_action=self.next_action_input.toPlainText().strip() or None,
        )

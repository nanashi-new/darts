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
        self.setWindowTitle("Новая training entry")
        self.resize(520, 460)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.coach_name_input = QLineEdit(self)
        self.coach_name_input.setText(default_coach_name or "")
        self.training_date_edit = QDateEdit(self)
        self.training_date_edit.setCalendarPopup(True)
        self.training_date_edit.setDate(QDate.currentDate())
        self.session_type_input = QLineEdit(self)
        self.summary_input = QLineEdit(self)
        self.goals_input = QTextEdit(self)
        self.goals_input.setMinimumHeight(90)
        self.metrics_input = QTextEdit(self)
        self.metrics_input.setPlaceholderText('{"doubles_hit": 10}')
        self.metrics_input.setMinimumHeight(80)
        self.next_action_input = QTextEdit(self)
        self.next_action_input.setMinimumHeight(80)

        form.addRow("Coach", self.coach_name_input)
        form.addRow("Date", self.training_date_edit)
        form.addRow("Session type", self.session_type_input)
        form.addRow("Summary*", self.summary_input)
        form.addRow("Goals", self.goals_input)
        form.addRow("Metrics JSON", self.metrics_input)
        form.addRow("Next action", self.next_action_input)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.accepted.connect(self._accept_if_valid)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _accept_if_valid(self) -> None:
        if not self.summary_input.text().strip():
            QMessageBox.warning(self, "Training", "Summary is required.")
            return
        metrics_text = self.metrics_input.toPlainText().strip()
        if metrics_text:
            try:
                metrics = json.loads(metrics_text)
            except json.JSONDecodeError:
                QMessageBox.warning(self, "Training", "Metrics must be valid JSON.")
                return
            if not isinstance(metrics, dict):
                QMessageBox.warning(self, "Training", "Metrics JSON must be an object.")
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

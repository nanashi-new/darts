from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
)


@dataclass(frozen=True)
class ManualAdultTournamentFormData:
    tournament_name: str
    tournament_date: str
    league_code: str | None
    rows: list[dict[str, object]]


class ManualTournamentDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("New adult tournament")
        self.resize(640, 520)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit(self)
        self.date_input = QDateEdit(self)
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setDisplayFormat("dd.MM.yyyy")
        self.league_input = QLineEdit(self)
        self.rows_input = QTextEdit(self)
        self.rows_input.setPlaceholderText(
            "One row per line:\n"
            "FIO; birth date or year; place; points_total\n"
            "Adultov Alex; 1989-01-01; 1; 120\n"
            "Senior Sara; 1990; 2; 105"
        )

        form.addRow("Название:", self.name_input)
        form.addRow("Дата:", self.date_input)
        form.addRow("Лига:", self.league_input)
        layout.addLayout(form)
        layout.addWidget(QLabel("Результаты:", self))
        layout.addWidget(self.rows_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.accepted.connect(self._accept_if_valid)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _accept_if_valid(self) -> None:
        try:
            self.form_data()
        except ValueError as exc:
            QMessageBox.warning(self, "Adult tournament", str(exc))
            return
        self.accept()

    def form_data(self) -> ManualAdultTournamentFormData:
        tournament_name = self.name_input.text().strip()
        if not tournament_name:
            raise ValueError("Введите название турнира.")

        rows = self._parse_rows()
        if not rows:
            raise ValueError("Добавьте хотя бы одну строку результата.")

        league_code = self.league_input.text().strip() or None
        return ManualAdultTournamentFormData(
            tournament_name=tournament_name,
            tournament_date=self.date_input.date().toString("yyyy-MM-dd"),
            league_code=league_code,
            rows=rows,
        )

    def _parse_rows(self) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for line_number, raw_line in enumerate(self.rows_input.toPlainText().splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue
            parts = [part.strip() for part in line.split(";")]
            if len(parts) < 4:
                raise ValueError(
                    f"Строка {line_number}: нужен формат 'ФИО; дата/год; место; очки'."
                )
            rows.append(
                {
                    "fio": parts[0],
                    "birth": parts[1] or None,
                    "place": parts[2],
                    "points_total": parts[3],
                }
            )
        return rows

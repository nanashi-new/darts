from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
)

ManualTournamentRow = dict[str, object]

@dataclass(frozen=True)
class ManualTournamentFormData:
    tournament_name: str
    tournament_date: str
    league_code: str | None
    rows: list[ManualTournamentRow]


class ManualTournamentDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Новый взрослый турнир")
        self.resize(620, 520)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Название турнира")
        self.date_input = QDateEdit(self)
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setDisplayFormat("dd.MM.yyyy")
        self.league_code_input = QLineEdit(self)
        self.league_code_input.setPlaceholderText("Код лиги, если нужен")
        self.rows_input = QPlainTextEdit(self)
        self.rows_input.setPlaceholderText(
            "Одна строка на участника:\n"
            "ФИО; дата или год рождения; место; очки\n"
            "Иванов Иван; 1989-01-01; 1; 120\n"
            "Петрова Анна; 1990; 2; 105"
        )
        self.rows_input.setMinimumHeight(260)

        form.addRow("Название*", self.name_input)
        form.addRow("Дата", self.date_input)
        form.addRow("Лига", self.league_code_input)
        form.addRow("Результаты*", self.rows_input)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        if save_button := buttons.button(QDialogButtonBox.StandardButton.Save):
            save_button.setText("Создать")
        if cancel_button := buttons.button(QDialogButtonBox.StandardButton.Cancel):
            cancel_button.setText("Отмена")
        buttons.accepted.connect(self._accept_if_valid)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _accept_if_valid(self) -> None:
        try:
            self.form_data()
        except ValueError as exc:
            QMessageBox.warning(self, "Взрослый турнир", str(exc))
            return
        self.accept()

    def form_data(self) -> ManualTournamentFormData:
        name = self.name_input.text().strip()
        if not name:
            raise ValueError("Укажите название турнира.")
        rows = self._parse_rows()
        if not rows:
            raise ValueError("Добавьте хотя бы одну строку результатов.")
        return ManualTournamentFormData(
            tournament_name=name,
            tournament_date=self.date_input.date().toString("yyyy-MM-dd"),
            league_code=self.league_code_input.text().strip() or None,
            rows=rows,
        )

    def _parse_rows(self) -> list[ManualTournamentRow]:
        rows: list[ManualTournamentRow] = []
        for line_number, raw_line in enumerate(self.rows_input.toPlainText().splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue
            parts = [part.strip() for part in line.split(";")]
            if len(parts) != 4:
                raise ValueError(f"Строка {line_number}: нужен формат 'ФИО; дата/год; место; очки'.")
            rows.append(
                {
                    "fio": parts[0],
                    "birth": parts[1] or None,
                    "place": parts[2],
                    "points_total": parts[3],
                }
            )
        return rows

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from app.db.database import get_connection
from app.services.recalculate_tournament import recalculate_all_tournaments


class ReportsView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._connection = get_connection()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Раздел «Отчёты»."))

        recalc_btn = QPushButton("Пересчитать всё", self)
        recalc_btn.clicked.connect(self._recalculate_all)
        layout.addWidget(recalc_btn)
        layout.addStretch(1)

    def _recalculate_all(self) -> None:
        report = recalculate_all_tournaments(connection=self._connection)
        QMessageBox.information(
            self,
            "Пересчитать всё",
            (
                f"Турниров: {report.tournaments_processed}\n"
                f"Обновлено результатов: {report.results_updated}\n"
                f"Warnings: {len(report.warnings)}\n"
                f"Errors: {len(report.errors)}"
            ),
        )

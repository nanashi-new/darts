from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from app.db.database import get_connection
from app.db.repositories import ResultRepository, TournamentRepository
from app.services.export_service import ExportService
from app.services.recalculate_tournament import recalculate_tournament_results


class TournamentsView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._connection = get_connection()
        self._tournament_repo = TournamentRepository(self._connection)
        self._result_repo = ResultRepository(self._connection)
        self._export_service = ExportService()
        self._current_tournament: dict[str, object] | None = None

        layout = QVBoxLayout(self)
        self.header_label = QLabel("Турниры пока не загружены.", self)
        layout.addWidget(self.header_label)

        self.results_table = QTableView(self)
        self.results_table.setSortingEnabled(False)
        layout.addWidget(self.results_table)
        layout.addLayout(self._build_actions())

        self.refresh_latest_tournament()

    def _build_actions(self) -> QHBoxLayout:
        actions_layout = QHBoxLayout()
        recalc_btn = QPushButton("Пересчитать турнир", self)
        export_pdf_btn = QPushButton("Export PDF", self)
        export_xlsx_btn = QPushButton("Export XLSX", self)
        print_btn = QPushButton("Print", self)

        recalc_btn.clicked.connect(self._recalculate_tournament)
        export_pdf_btn.clicked.connect(self._export_pdf)
        export_xlsx_btn.clicked.connect(self._export_xlsx)
        print_btn.clicked.connect(self._print_table)

        for button in (recalc_btn, export_pdf_btn, export_xlsx_btn, print_btn):
            actions_layout.addWidget(button)

        actions_layout.addStretch(1)
        return actions_layout

    def refresh_latest_tournament(self, tournament_id: int | None = None) -> None:
        tournament = (
            self._tournament_repo.get(tournament_id)
            if tournament_id is not None
            else self._tournament_repo.get_latest()
        )
        if not tournament:
            self._current_tournament = None
            self.header_label.setText("Турниры пока не загружены.")
            self.results_table.setModel(QStandardItemModel(self))
            return

        self._current_tournament = tournament
        date_label = tournament.get("date") or "дата не указана"
        category_label = tournament.get("category_code") or "категория не указана"
        self.header_label.setText(
            f"Турнир: {tournament.get('name')} — {date_label} ({category_label})"
        )

        results = self._result_repo.list_with_players(int(tournament["id"]))
        self._set_results_table(results)

    def _set_results_table(self, results: list[dict[str, object]]) -> None:
        header_order = [
            ("place", "Место"),
            ("fio", "ФИО"),
            ("birth_date", "Дата рождения"),
            ("score_set", "Набор очков"),
            ("score_sector20", "Сектор 20"),
            ("score_big_round", "Большой раунд"),
            ("points_place", "Очки за место"),
            ("points_classification", "Очки классификации"),
            ("points_total", "Итого"),
        ]
        model = QStandardItemModel(self)
        model.setColumnCount(len(header_order))
        model.setHorizontalHeaderLabels([label for _, label in header_order])

        for result in results:
            last_name = result.get("last_name") or ""
            first_name = result.get("first_name") or ""
            middle_name = result.get("middle_name") or ""
            fio = " ".join(part for part in [last_name, first_name, middle_name] if part)
            row_items = []
            row_data = {
                **result,
                "fio": fio,
            }
            for key, _ in header_order:
                value = row_data.get(key)
                display = "" if value is None else str(value)
                row_items.append(QStandardItem(display))
            model.appendRow(row_items)

        self.results_table.setModel(model)
        self.results_table.resizeColumnsToContents()

    def _export_pdf(self) -> None:
        if not self._current_tournament:
            QMessageBox.warning(self, "Экспорт протокола", "Турнир не выбран.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт протокола в PDF",
            "tournament_protocol.pdf",
            "PDF Files (*.pdf)",
        )
        if not path:
            QMessageBox.warning(self, "Экспорт протокола", "Путь для сохранения не выбран.")
            return
        try:
            self._export_service.export_table_pdf(
                self.results_table, path, self._build_export_header()
            )
        except OSError as exc:
            QMessageBox.critical(self, "Экспорт протокола", str(exc))
            return
        QMessageBox.information(self, "Экспорт протокола", f"Готово: {path}")

    def _export_xlsx(self) -> None:
        if not self._current_tournament:
            QMessageBox.warning(self, "Экспорт протокола", "Турнир не выбран.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт протокола в XLSX",
            "tournament_protocol.xlsx",
            "Excel Files (*.xlsx)",
        )
        if not path:
            QMessageBox.warning(self, "Экспорт протокола", "Путь для сохранения не выбран.")
            return
        try:
            self._export_service.export_table_xlsx(
                self.results_table, path, self._build_export_header()
            )
        except OSError as exc:
            QMessageBox.critical(self, "Экспорт протокола", str(exc))
            return
        QMessageBox.information(self, "Экспорт протокола", f"Готово: {path}")

    def _print_table(self) -> None:
        if not self._current_tournament:
            QMessageBox.warning(self, "Печать", "Турнир не выбран.")
            return
        if self._export_service.print_table(
            self.results_table, self, self._build_export_header()
        ):
            QMessageBox.information(self, "Печать", "Печать отправлена на принтер.")

    def _recalculate_tournament(self) -> None:
        if not self._current_tournament:
            QMessageBox.warning(self, "Пересчет", "Турнир не выбран.")
            return
        tournament_id = int(self._current_tournament["id"])
        try:
            norms_loaded = recalculate_tournament_results(
                connection=self._connection,
                tournament_id=tournament_id,
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Пересчет", str(exc))
            return
        if not norms_loaded:
            QMessageBox.warning(self, "Пересчет", "Нормативы не загружены.")
        self.refresh_latest_tournament(tournament_id)
        QMessageBox.information(self, "Пересчет", "Пересчет завершен.")

    def _build_export_header(self) -> list[str]:
        if not self._current_tournament:
            return []
        name = self._current_tournament.get("name") or "Название не указано"
        date_label = self._current_tournament.get("date") or "дата не указана"
        category_label = (
            self._current_tournament.get("category_code") or "категория не указана"
        )
        return [
            f"Турнир: {name}",
            f"Дата: {date_label}",
            f"Категория: {category_label}",
        ]

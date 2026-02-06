from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
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
        self._format_combo = QComboBox(self)
        self._format_combo.addItems(["PDF", "XLSX", "PNG"])
        self._image_mode_combo = QComboBox(self)
        self._image_mode_combo.addItems(["Сохранить видимую область", "Сохранить всю таблицу"])
        export_btn = QPushButton("Экспорт", self)
        print_btn = QPushButton("Печать", self)

        recalc_btn.clicked.connect(self._recalculate_tournament)
        export_btn.clicked.connect(self._export_selected_format)
        print_btn.clicked.connect(self._print_table)

        actions_layout.addWidget(recalc_btn)
        actions_layout.addWidget(QLabel("Формат:"))
        actions_layout.addWidget(self._format_combo)
        actions_layout.addWidget(self._image_mode_combo)
        actions_layout.addWidget(export_btn)
        actions_layout.addWidget(print_btn)

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

    def _export_selected_format(self) -> None:
        if not self._current_tournament:
            QMessageBox.warning(self, "Экспорт протокола", "Турнир не выбран.")
            return
        selected_format = self._format_combo.currentText().lower()
        defaults = {
            "pdf": "tournament_protocol.pdf",
            "xlsx": "tournament_protocol.xlsx",
            "png": "tournament_protocol.png",
        }
        filters = {
            "pdf": "PDF Files (*.pdf)",
            "xlsx": "Excel Files (*.xlsx)",
            "png": "Image Files (*.png *.jpg)",
        }
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт протокола",
            defaults[selected_format],
            filters[selected_format],
        )
        if not path:
            QMessageBox.warning(self, "Экспорт протокола", "Путь для сохранения не выбран.")
            return

        if selected_format == "png" and not path.lower().endswith((".png", ".jpg", ".jpeg")):
            chosen_extension, accepted = QInputDialog.getItem(
                self,
                "Формат изображения",
                "Расширение:",
                ["png", "jpg"],
                editable=False,
            )
            if not accepted:
                return
            path = f"{path}.{chosen_extension}"

        try:
            if selected_format in {"pdf", "xlsx"}:
                self._export_service.export_dataset(
                    export_format=selected_format,
                    path=path,
                    header_lines=self._build_export_header(),
                    columns=[
                        "Место",
                        "ФИО",
                        "Дата рождения",
                        "Набор очков",
                        "Сектор 20",
                        "Большой раунд",
                        "Очки за место",
                        "Очки классификации",
                        "Итого",
                    ],
                    rows=self._table_rows(),
                )
            else:
                full_table = self._image_mode_combo.currentIndex() == 1
                self._export_service.save_table_image(self.results_table, path, full_table=full_table)
        except (OSError, ValueError) as exc:
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
            report = recalculate_tournament_results(
                connection=self._connection,
                tournament_id=tournament_id,
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Пересчет", str(exc))
            return
        self.refresh_latest_tournament(tournament_id)
        details = [
            f"Обновлено результатов: {report.results_updated}",
            f"Warnings: {len(report.warnings)}",
            f"Errors: {len(report.errors)}",
        ]
        if report.warnings:
            details.append("\n".join(report.warnings[:3]))
        if report.errors:
            details.append("\n".join(report.errors[:3]))
        QMessageBox.information(self, "Пересчет", "\n".join(details))

    def _table_rows(self) -> list[list[str]]:
        model = self.results_table.model()
        if model is None:
            return []
        rows: list[list[str]] = []
        for row in range(model.rowCount()):
            rows.append([str(model.index(row, column).data() or "") for column in range(model.columnCount())])
        return rows

    def _build_export_header(self) -> list[str]:
        if not self._current_tournament:
            return []
        name = self._current_tournament.get("name") or "Название не указано"
        date_label = self._current_tournament.get("date") or "дата не указана"
        category_label = (
            self._current_tournament.get("category_code") or "категория не указана"
        )
        return [
            "Протокол турнира",
            f"Турнир: {name}",
            f"Дата: {date_label}",
            f"Категория: {category_label}",
            "N: 6",
        ]

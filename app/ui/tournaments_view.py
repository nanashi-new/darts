from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QLabel, QTableView, QVBoxLayout, QWidget

from app.db.database import get_connection
from app.db.repositories import ResultRepository, TournamentRepository


class TournamentsView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._connection = get_connection()
        self._tournament_repo = TournamentRepository(self._connection)
        self._result_repo = ResultRepository(self._connection)

        layout = QVBoxLayout(self)
        self.header_label = QLabel("Турниры пока не загружены.", self)
        layout.addWidget(self.header_label)

        self.results_table = QTableView(self)
        self.results_table.setSortingEnabled(False)
        layout.addWidget(self.results_table)

        self.refresh_latest_tournament()

    def refresh_latest_tournament(self, tournament_id: int | None = None) -> None:
        tournament = (
            self._tournament_repo.get(tournament_id)
            if tournament_id is not None
            else self._tournament_repo.get_latest()
        )
        if not tournament:
            self.header_label.setText("Турниры пока не загружены.")
            self.results_table.setModel(QStandardItemModel(self))
            return

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

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from app.db.database import get_connection
from app.db.repositories import ResultRepository, TournamentRepository


@dataclass
class RatingRow:
    place: int
    fio: str
    points: int
    tournaments_count: int


class RatingView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._connection = get_connection()
        self._tournament_repo = TournamentRepository(self._connection)
        self._result_repo = ResultRepository(self._connection)

        root_layout = QVBoxLayout(self)
        root_layout.addLayout(self._build_filters())

        self._table = QTableView(self)
        self._table.setSortingEnabled(False)
        root_layout.addWidget(self._table)

        root_layout.addLayout(self._build_actions())
        self._refresh_table()

    def _build_filters(self) -> QHBoxLayout:
        filters_layout = QHBoxLayout()
        filters_box = QGroupBox("Фильтры", self)
        filters_layout.addWidget(filters_box)

        grid = QGridLayout(filters_box)

        self._category_combo = QComboBox(filters_box)
        self._category_combo.addItem("Все категории", None)
        for category in self._tournament_repo.list_category_codes():
            self._category_combo.addItem(category, category)

        self._n_spin = QSpinBox(filters_box)
        self._n_spin.setRange(3, 12)
        self._n_spin.setValue(6)
        self._n_spin.setSuffix(" турниров")

        self._search_input = QLineEdit(filters_box)
        self._search_input.setPlaceholderText("Поиск по ФИО")

        grid.addWidget(QLabel("Категория:"), 0, 0)
        grid.addWidget(self._category_combo, 0, 1)
        grid.addWidget(QLabel("N (3–12):"), 0, 2)
        grid.addWidget(self._n_spin, 0, 3)
        grid.addWidget(QLabel("ФИО:"), 0, 4)
        grid.addWidget(self._search_input, 0, 5)

        self._category_combo.currentIndexChanged.connect(self._refresh_table)
        self._n_spin.valueChanged.connect(self._refresh_table)
        self._search_input.textChanged.connect(self._refresh_table)

        filters_layout.addStretch(1)
        return filters_layout

    def _build_actions(self) -> QHBoxLayout:
        actions_layout = QHBoxLayout()

        export_pdf_btn = QPushButton("Export PDF", self)
        export_xlsx_btn = QPushButton("Export XLSX", self)
        print_btn = QPushButton("Print", self)
        save_image_btn = QPushButton("Save as Image", self)

        for button in (export_pdf_btn, export_xlsx_btn, print_btn, save_image_btn):
            button.setEnabled(False)
            actions_layout.addWidget(button)

        actions_layout.addStretch(1)
        return actions_layout

    def _refresh_table(self) -> None:
        category_code = self._category_combo.currentData()
        search_term = self._search_input.text().strip()
        n_value = int(self._n_spin.value())

        raw_results = self._result_repo.list_results_for_rating(
            category_code=category_code,
            search_term=search_term or None,
        )

        rating_rows = self._calculate_rating_rows(raw_results, n_value)
        self._set_table(rating_rows)

    @staticmethod
    def _calculate_rating_rows(
        results: list[dict[str, object]], n_value: int
    ) -> list[RatingRow]:
        players: dict[int, dict[str, object]] = {}
        for entry in results:
            player_id = int(entry["player_id"])
            players.setdefault(player_id, {"entries": [], "fio": ""})
            players[player_id]["entries"].append(entry)

            last_name = str(entry.get("last_name") or "")
            first_name = str(entry.get("first_name") or "")
            middle_name = str(entry.get("middle_name") or "")
            fio = " ".join(part for part in [last_name, first_name, middle_name] if part)
            players[player_id]["fio"] = fio

        rating_rows: list[RatingRow] = []
        for player in players.values():
            entries = player["entries"]
            points_list = [int(entry.get("points_total") or 0) for entry in entries]
            points_sum = sum(points_list[:n_value])
            tournaments_count = min(len(points_list), n_value)
            rating_rows.append(
                RatingRow(
                    place=0,
                    fio=str(player["fio"]),
                    points=points_sum,
                    tournaments_count=tournaments_count,
                )
            )

        rating_rows.sort(key=lambda row: (-row.points, row.fio))
        for index, row in enumerate(rating_rows, start=1):
            row.place = index
        return rating_rows

    def _set_table(self, rows: list[RatingRow]) -> None:
        header_order = [
            ("place", "Место"),
            ("fio", "ФИО"),
            ("points", "Очки"),
            ("tournaments_count", "Учтено турниров"),
        ]
        model = QStandardItemModel(self)
        model.setColumnCount(len(header_order))
        model.setHorizontalHeaderLabels([label for _, label in header_order])

        for row in rows:
            row_items = []
            row_data = {
                "place": row.place,
                "fio": row.fio,
                "points": row.points,
                "tournaments_count": row.tournaments_count,
            }
            for key, _ in header_order:
                value = row_data.get(key)
                display = "" if value is None else str(value)
                item = QStandardItem(display)
                item.setTextAlignment(Qt.AlignCenter)
                row_items.append(item)
            model.appendRow(row_items)

        self._table.setModel(model)
        self._table.resizeColumnsToContents()

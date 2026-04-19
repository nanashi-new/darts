from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from app.db.database import get_connection
from app.db.repositories import ResultRepository, TournamentRepository
from app.domain.rating import RatingSnapshotRow, build_rating_snapshot
from app.services.audit_log import AuditLogService, ERROR, EXPORT_FILE
from app.services.export_service import ExportService
from app.ui.rating_history_dialog import RatingHistoryDialog


class RatingView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._connection = get_connection()
        self._tournament_repo = TournamentRepository(self._connection)
        self._result_repo = ResultRepository(self._connection)
        self._export_service = ExportService()
        self._audit_log_service = AuditLogService(self._connection)

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
        self._category_combo.currentIndexChanged.connect(self._refresh_history_button_state)
        self._n_spin.valueChanged.connect(self._refresh_table)
        self._search_input.textChanged.connect(self._refresh_table)

        filters_layout.addStretch(1)
        return filters_layout

    def _build_actions(self) -> QHBoxLayout:
        actions_layout = QHBoxLayout()

        self._format_combo = QComboBox(self)
        self._format_combo.addItems(["PDF", "XLSX", "PNG"])
        self._image_mode_combo = QComboBox(self)
        self._image_mode_combo.addItems(["Сохранить видимую область", "Сохранить всю таблицу"])

        export_btn = QPushButton("Экспорт", self)
        print_btn = QPushButton("Печать", self)
        self._history_button = QPushButton("История рейтинга", self)

        export_btn.clicked.connect(self._export_selected_format)
        print_btn.clicked.connect(self._print_table)
        self._history_button.clicked.connect(self._open_rating_history)

        actions_layout.addWidget(QLabel("Формат:"))
        actions_layout.addWidget(self._format_combo)
        actions_layout.addWidget(self._image_mode_combo)
        actions_layout.addWidget(export_btn)
        actions_layout.addWidget(print_btn)
        actions_layout.addWidget(self._history_button)

        actions_layout.addStretch(1)
        self._refresh_history_button_state()
        return actions_layout

    def _refresh_table(self) -> None:
        category_code = self._category_combo.currentData()
        search_term = self._search_input.text().strip()
        n_value = int(self._n_spin.value())

        raw_results = self._result_repo.list_results_for_rating(
            category_code=category_code,
            search_term=search_term or None,
        )

        rating_rows = build_rating_snapshot(raw_results, n_value)
        self._set_table(rating_rows)

    def _set_table(self, rows: list[RatingSnapshotRow]) -> None:
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

    def _export_selected_format(self) -> None:
        selected_format = self._format_combo.currentText().lower()
        defaults = {"pdf": "rating.pdf", "xlsx": "rating.xlsx", "png": "rating.png"}
        filters = {
            "pdf": "PDF Files (*.pdf)",
            "xlsx": "Excel Files (*.xlsx)",
            "png": "Image Files (*.png *.jpg)",
        }
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт рейтинга",
            defaults[selected_format],
            filters[selected_format],
        )
        if not path:
            QMessageBox.warning(self, "Экспорт рейтинга", "Путь для сохранения не выбран.")
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
                    columns=["Место", "ФИО", "Очки", "Учтено турниров"],
                    rows=self._table_rows(),
                )
            else:
                full_table = self._image_mode_combo.currentIndex() == 1
                self._export_service.save_table_image(self._table, path, full_table=full_table)
        except (OSError, ValueError) as exc:
            self._audit_log_service.log_event(
                ERROR,
                "Ошибка экспорта рейтинга",
                str(exc),
                level="error",
                context={"path": path, "format": selected_format},
            )
            QMessageBox.critical(self, "Экспорт рейтинга", str(exc))
            return
        self._audit_log_service.log_event(
            EXPORT_FILE,
            "Экспорт рейтинга",
            f"Формат: {selected_format}; путь: {path}",
            context={"path": path, "format": selected_format},
        )
        QMessageBox.information(self, "Экспорт рейтинга", f"Готово: {path}")

    def _print_table(self) -> None:
        if self._export_service.print_table(self._table, self, self._build_export_header()):
            QMessageBox.information(self, "Печать", "Печать отправлена на принтер.")

    def _table_rows(self) -> list[list[str]]:
        model = self._table.model()
        if model is None:
            return []
        rows: list[list[str]] = []
        for row in range(model.rowCount()):
            rows.append([str(model.index(row, column).data() or "") for column in range(model.columnCount())])
        return rows

    def _build_export_header(self) -> list[str]:
        date_label = self._export_service.format_date_label()
        category = self._category_combo.currentText()
        n_value = self._n_spin.value()
        return [
            "Рейтинг",
            f"Дата: {date_label}",
            f"Категория: {category}",
            f"N: {n_value}",
        ]

    def _refresh_history_button_state(self) -> None:
        category_code = self._category_combo.currentData()
        is_enabled = bool(category_code)
        self._history_button.setEnabled(is_enabled)
        if is_enabled:
            self._history_button.setToolTip("")
            return
        self._history_button.setToolTip("Выберите категорию, чтобы открыть историю рейтинга.")

    def _open_rating_history(self) -> None:
        category_code = self._category_combo.currentData()
        if not category_code:
            QMessageBox.information(self, "История рейтинга", "Сначала выберите категорию.")
            return
        dialog = RatingHistoryDialog(
            connection=self._connection,
            scope_type="category",
            scope_key=str(category_code),
            parent=self,
        )
        dialog.exec()

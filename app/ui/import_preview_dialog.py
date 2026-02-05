from __future__ import annotations

from typing import Iterable

from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QTableView,
    QVBoxLayout,
)


class ImportPreviewDialog(QDialog):
    def __init__(
        self,
        rows: Iterable[dict[str, object]],
        warnings: Iterable[str],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Предпросмотр импорта")
        self.resize(900, 500)

        layout = QVBoxLayout(self)

        self.table_view = QTableView(self)
        self.table_view.setSortingEnabled(False)

        self.warning_list = QListWidget(self)
        self.warning_label = QLabel("Предупреждения:", self)

        layout.addWidget(self.table_view)
        layout.addWidget(self.warning_label)
        layout.addWidget(self.warning_list)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self._set_table(rows)
        self._set_warnings(list(warnings))

    def _set_table(self, rows: Iterable[dict[str, object]]) -> None:
        header_order = [
            ("fio", "ФИО"),
            ("birth", "Дата рождения"),
            ("coach", "Тренер"),
            ("place", "Место"),
            ("score_set", "Набор очков"),
            ("score_sector20", "Сектор 20"),
            ("score_big_round", "Большой раунд"),
        ]
        model = QStandardItemModel(self)
        model.setColumnCount(len(header_order))
        model.setHorizontalHeaderLabels([label for _, label in header_order])

        for row in rows:
            items = []
            for key, _ in header_order:
                value = row.get(key)
                display = "" if value is None else str(value)
                items.append(QStandardItem(display))
            model.appendRow(items)

        self.table_view.setModel(model)
        self.table_view.resizeColumnsToContents()

    def _set_warnings(self, warnings: list[str]) -> None:
        if not warnings:
            self.warning_list.addItem("Предупреждений нет.")
            return
        for warning in warnings:
            self.warning_list.addItem(warning)

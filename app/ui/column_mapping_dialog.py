from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QTableView,
    QVBoxLayout,
)


class ColumnMappingDialog(QDialog):
    def __init__(
        self,
        headers: Iterable[str],
        preview_rows: Iterable[Iterable[object]],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Сопоставление колонок")
        self.resize(950, 560)

        self._headers = [str(item) for item in headers]
        self._required = ("fio", "place", "score_set")
        self._labels = {
            "fio": "ФИО",
            "birth_year": "Год рождения",
            "birth_date": "Дата рождения",
            "place": "Место",
            "score_set": "Набор очков",
            "score_sector20": "Сектор 20",
            "score_big_round": "Большой раунд",
        }

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Проверьте заголовки и назначьте колонки для полей импорта.", self))

        self.table_view = QTableView(self)
        self.table_view.setSortingEnabled(False)
        self._set_preview_table(self._headers, preview_rows)
        layout.addWidget(self.table_view)

        form = QFormLayout()
        self._combos: dict[str, QComboBox] = {}
        for key in (
            "fio",
            "birth_year",
            "birth_date",
            "place",
            "score_set",
            "score_sector20",
            "score_big_round",
        ):
            combo = QComboBox(self)
            combo.addItem("— не выбрано —", "")
            for header in self._headers:
                combo.addItem(header, header)
            combo.currentIndexChanged.connect(self._update_status)
            self._combos[key] = combo
            form.addRow(f"{self._labels[key]}:", combo)

        layout.addLayout(form)

        self.status_label = QLabel(self)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        self.ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._guess_initial_mapping()
        self._update_status()

    def mapping(self) -> dict[str, str]:
        mapped: dict[str, str] = {}
        for key, combo in self._combos.items():
            value = str(combo.currentData(Qt.ItemDataRole.UserRole) or "")
            if value:
                mapped[key] = value
        return mapped

    def _guess_initial_mapping(self) -> None:
        normalized_headers = {self._normalize(h): h for h in self._headers}
        hints = {
            "fio": ("фио", "игрок", "player", "фамилия"),
            "birth_year": ("год", "year"),
            "birth_date": ("датарождения", "birth", "др"),
            "place": ("место", "place", "позиция"),
            "score_set": ("очки", "набор", "score"),
            "score_sector20": ("сектор20", "sector20", "с20"),
            "score_big_round": ("большойраунд", "biground", "бр"),
        }
        for key, keywords in hints.items():
            for normalized, header in normalized_headers.items():
                if any(keyword in normalized for keyword in keywords):
                    combo = self._combos[key]
                    index = combo.findData(header)
                    if index >= 0:
                        combo.setCurrentIndex(index)
                    break

    @staticmethod
    def _normalize(value: object) -> str:
        text = str(value).strip().lower()
        return "".join(ch for ch in text if ch.isalnum())

    def _update_status(self) -> None:
        mapping = self.mapping()
        missing = [self._labels[key] for key in self._required if not mapping.get(key)]
        if missing:
            self.status_label.setText(
                "Не назначены обязательные колонки: " + ", ".join(missing)
            )
            self.ok_button.setEnabled(False)
            return
        self.status_label.setText("Все обязательные колонки назначены.")
        self.ok_button.setEnabled(True)

    def _set_preview_table(self, headers: list[str], rows: Iterable[Iterable[object]]) -> None:
        model = QStandardItemModel(self)
        model.setColumnCount(len(headers))
        model.setHorizontalHeaderLabels(headers)
        for row in rows:
            items = [QStandardItem("" if value is None else str(value)) for value in row]
            model.appendRow(items)
        self.table_view.setModel(model)
        self.table_view.resizeColumnsToContents()

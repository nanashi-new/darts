"""Dialog for computing and applying season league transitions."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.db.database import get_connection
from app.services.season_transfer import (
    SeasonTransferPreview,
    apply_season_transfers,
    compute_season_transfer_candidates,
)


class SeasonTransferDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Сезонные переходы между лигами")
        self.resize(800, 600)
        self._connection = get_connection()
        self._preview: SeasonTransferPreview | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Inputs row
        inputs_layout = QHBoxLayout()
        inputs_layout.addWidget(QLabel("Премьер:"))
        self._premier_input = QLineEdit("PREMIER")
        self._premier_input.setMaximumWidth(120)
        inputs_layout.addWidget(self._premier_input)

        inputs_layout.addWidget(QLabel("Первая:"))
        self._first_input = QLineEdit("FIRST")
        self._first_input.setMaximumWidth(120)
        inputs_layout.addWidget(self._first_input)

        inputs_layout.addWidget(QLabel("N:"))
        self._n_spin = QSpinBox()
        self._n_spin.setMinimum(1)
        self._n_spin.setMaximum(20)
        self._n_spin.setValue(3)
        inputs_layout.addWidget(self._n_spin)

        inputs_layout.addWidget(QLabel("Переходов:"))
        self._transfer_count_spin = QSpinBox()
        self._transfer_count_spin.setMinimum(1)
        self._transfer_count_spin.setMaximum(20)
        self._transfer_count_spin.setValue(4)
        inputs_layout.addWidget(self._transfer_count_spin)

        inputs_layout.addStretch()
        layout.addLayout(inputs_layout)

        # Calculate button
        self._calc_btn = QPushButton("Рассчитать")
        self._calc_btn.setToolTip("Рассчитать кандидатов на переход по текущему рейтингу.")
        self._calc_btn.clicked.connect(self._on_calculate)
        layout.addWidget(self._calc_btn)

        # Warnings label
        self._warnings_label = QLabel("")
        self._warnings_label.setWordWrap(True)
        self._warnings_label.setStyleSheet("color: red;")
        self._warnings_label.setVisible(False)
        layout.addWidget(self._warnings_label)

        # Tables side by side
        tables_layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Вылет из Премьер (нижние)"))
        self._relegated_table = QTableWidget()
        self._relegated_table.setColumnCount(3)
        self._relegated_table.setHorizontalHeaderLabels(["ФИО", "Очки", "Позиция"])
        self._relegated_table.horizontalHeader().setStretchLastSection(True)
        left_layout.addWidget(self._relegated_table)
        tables_layout.addLayout(left_layout)

        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Повышение в Премьер (верхние)"))
        self._promoted_table = QTableWidget()
        self._promoted_table.setColumnCount(3)
        self._promoted_table.setHorizontalHeaderLabels(["ФИО", "Очки", "Позиция"])
        self._promoted_table.horizontalHeader().setStretchLastSection(True)
        right_layout.addWidget(self._promoted_table)
        tables_layout.addLayout(right_layout)

        layout.addLayout(tables_layout)

        # Apply button
        self._apply_btn = QPushButton("Применить переходы")
        self._apply_btn.setToolTip(
            "Применить рассчитанные переходы. Точка восстановления будет создана автоматически."
        )
        self._apply_btn.setEnabled(False)
        self._apply_btn.clicked.connect(self._on_apply)
        layout.addWidget(self._apply_btn)

        # Close button
        button_box = QDialogButtonBox()
        close_btn = button_box.addButton("Закрыть", QDialogButtonBox.ButtonRole.RejectRole)
        close_btn.clicked.connect(self.reject)
        layout.addWidget(button_box)

    def _on_calculate(self) -> None:
        premier_code = self._premier_input.text().strip() or "PREMIER"
        first_code = self._first_input.text().strip() or "FIRST"
        n = self._n_spin.value()
        transfer_count = self._transfer_count_spin.value()

        self._preview = compute_season_transfer_candidates(
            connection=self._connection,
            premier_league_code=premier_code,
            first_league_code=first_code,
            n=n,
            transfer_count=transfer_count,
        )

        self._populate_tables()

        if self._preview.warnings:
            self._warnings_label.setText("\n".join(self._preview.warnings))
            self._warnings_label.setVisible(True)
        else:
            self._warnings_label.setVisible(False)

        if not self._preview.available:
            self._apply_btn.setEnabled(False)
            QMessageBox.information(
                self,
                "Расчет невозможен",
                self._preview.reason or "Расчет недоступен.",
            )
        else:
            self._apply_btn.setEnabled(True)

    def _populate_tables(self) -> None:
        preview = self._preview
        if preview is None:
            return

        self._relegated_table.setRowCount(len(preview.relegated))
        for i, candidate in enumerate(preview.relegated):
            self._relegated_table.setItem(i, 0, QTableWidgetItem(candidate.fio))
            self._relegated_table.setItem(i, 1, QTableWidgetItem(str(candidate.rating_points)))
            self._relegated_table.setItem(i, 2, QTableWidgetItem(str(candidate.rating_position)))

        self._promoted_table.setRowCount(len(preview.promoted))
        for i, candidate in enumerate(preview.promoted):
            self._promoted_table.setItem(i, 0, QTableWidgetItem(candidate.fio))
            self._promoted_table.setItem(i, 1, QTableWidgetItem(str(candidate.rating_points)))
            self._promoted_table.setItem(i, 2, QTableWidgetItem(str(candidate.rating_position)))

    def _on_apply(self) -> None:
        if self._preview is None or not self._preview.available:
            return

        reply = QMessageBox.warning(
            self,
            "Подтверждение",
            "Вы уверены? Будет выполнен обмен игроков между лигами. "
            "Точка восстановления будет создана автоматически.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        result = apply_season_transfers(
            connection=self._connection,
            preview=self._preview,
        )
        QMessageBox.information(
            self,
            "Готово",
            f"Применено переходов: {result.applied_count}.",
        )
        self._apply_btn.setEnabled(False)

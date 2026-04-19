from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.services.import_review import ImportRatingImpactPreview
from app.services.import_xlsx import ImportApplyReport


def _display_int(value: int | None) -> str:
    return "" if value is None else str(value)


class ImportApplyReviewDialog(QDialog):
    def __init__(
        self,
        *,
        apply_report: ImportApplyReport,
        rating_preview: ImportRatingImpactPreview,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Импорт завершён: review/apply")
        self.resize(780, 640)

        layout = QVBoxLayout(self)
        layout.addWidget(self._build_summary_group(apply_report))
        layout.addWidget(self._build_warnings_group(apply_report))
        layout.addWidget(self._build_rating_group(rating_preview))

        buttons = QDialogButtonBox(self)
        self.leave_button = QPushButton("Оставить draft", self)
        self.publish_button = QPushButton("Опубликовать сейчас", self)
        buttons.addButton(self.leave_button, QDialogButtonBox.ButtonRole.RejectRole)
        buttons.addButton(self.publish_button, QDialogButtonBox.ButtonRole.AcceptRole)
        self.leave_button.clicked.connect(self.reject)
        self.publish_button.clicked.connect(self.accept)
        layout.addWidget(buttons)

    def _build_summary_group(self, apply_report: ImportApplyReport) -> QGroupBox:
        group = QGroupBox("Сводка", self)
        layout = QVBoxLayout(group)

        self.summary_list = QListWidget(group)
        summary_lines = [
            "Данные применены в черновик турнира.",
            f"Турнир: {apply_report.tournament_name} (ID: {apply_report.tournament_id})",
            f"Статус: {apply_report.tournament_status}; has_draft_changes={int(apply_report.has_draft_changes)}",
            (
                f"Строки: прочитано {apply_report.rows_read}, "
                f"импортировано {apply_report.imported_rows} из {apply_report.total_rows}"
            ),
            (
                f"Игроки: создано {apply_report.players_created}, "
                f"переиспользовано {apply_report.players_reused}, "
                f"ручных сопоставлений {apply_report.players_matched_manually}"
            ),
            f"Файлов: {apply_report.files_processed}; таблиц: {apply_report.tables_processed}",
        ]
        if apply_report.skipped_rows:
            summary_lines.append(f"Пропущено строк: {apply_report.skipped_rows}")
        if apply_report.source_files:
            summary_lines.append(f"Источник: {', '.join(apply_report.source_files)}")
        for line in summary_lines:
            self.summary_list.addItem(QListWidgetItem(line))

        layout.addWidget(self.summary_list)
        return group

    def _build_warnings_group(self, apply_report: ImportApplyReport) -> QGroupBox:
        group = QGroupBox("Предупреждения", self)
        layout = QVBoxLayout(group)

        self.warnings_list = QListWidget(group)
        warning_lines = list(apply_report.warnings)
        if not apply_report.norms_loaded:
            warning_lines.insert(0, "Нормативы не загружены.")
        if not warning_lines:
            warning_lines.append("Предупреждений нет.")
        for warning in warning_lines:
            self.warnings_list.addItem(QListWidgetItem(warning))

        layout.addWidget(self.warnings_list)
        return group

    def _build_rating_group(self, rating_preview: ImportRatingImpactPreview) -> QGroupBox:
        group = QGroupBox("Rating Impact Preview", self)
        layout = QVBoxLayout(group)

        self.rating_status_label = QLabel(group)
        self.rating_status_label.setWordWrap(True)
        if rating_preview.available:
            if rating_preview.rows:
                self.rating_status_label.setText(
                    "Показаны игроки, у которых после публикации изменятся место или очки."
                )
            else:
                self.rating_status_label.setText(
                    "После публикации текущего draft официальный рейтинг не изменится."
                )
        else:
            self.rating_status_label.setText(rating_preview.reason or "Preview недоступен.")
        layout.addWidget(self.rating_status_label)

        self.impact_table = QTableWidget(0, 7, group)
        self.impact_table.setHorizontalHeaderLabels(
            [
                "Игрок",
                "Было место",
                "Станет место",
                "Δ место",
                "Было очков",
                "Станет очков",
                "Δ очков",
            ]
        )
        self.impact_table.verticalHeader().setVisible(False)
        self.impact_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.impact_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.impact_table.setAlternatingRowColors(True)
        header = self.impact_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in range(1, self.impact_table.columnCount()):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)

        for impact_row in rating_preview.rows:
            row_index = self.impact_table.rowCount()
            self.impact_table.insertRow(row_index)
            values = [
                impact_row.fio,
                _display_int(impact_row.old_place),
                _display_int(impact_row.new_place),
                _display_int(impact_row.place_delta),
                str(impact_row.old_points),
                str(impact_row.new_points),
                str(impact_row.points_delta),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if column == 0:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.impact_table.setItem(row_index, column, item)

        layout.addWidget(self.impact_table)
        return group

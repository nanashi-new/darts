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
from app.services.league_transfer import LeagueTransferPreview
from app.ui.labels import tournament_status_label


def _display_int(value: int | None) -> str:
    return "" if value is None else str(value)


class ImportApplyReviewDialog(QDialog):
    def __init__(
        self,
        *,
        apply_report: ImportApplyReport,
        rating_preview: ImportRatingImpactPreview,
        league_preview: LeagueTransferPreview | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Импорт применен: проверка перед публикацией")
        self.resize(780, 640)

        layout = QVBoxLayout(self)
        layout.addWidget(self._build_summary_group(apply_report))
        layout.addWidget(self._build_warnings_group(apply_report))
        layout.addWidget(self._build_rating_group(rating_preview))
        layout.addWidget(self._build_league_group(league_preview))

        buttons = QDialogButtonBox(self)
        self.leave_button = QPushButton("Оставить черновиком", self)
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
            (
                f"Статус: {tournament_status_label(apply_report.tournament_status)}; "
                f"черновые изменения: {'да' if apply_report.has_draft_changes else 'нет'}"
            ),
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
        group = QGroupBox("Предпросмотр влияния на рейтинг", self)
        layout = QVBoxLayout(group)

        self.rating_status_label = QLabel(group)
        self.rating_status_label.setWordWrap(True)
        if rating_preview.available:
            if rating_preview.rows:
                self.rating_status_label.setText(
                    "Показаны игроки, у которых после публикации изменится место или количество очков."
                )
            else:
                self.rating_status_label.setText(
                    "После публикации текущего черновика официальный рейтинг не изменится."
                )
        else:
            self.rating_status_label.setText(rating_preview.reason or "Предпросмотр недоступен.")
        layout.addWidget(self.rating_status_label)

        self.impact_table = QTableWidget(0, 7, group)
        self.impact_table.setHorizontalHeaderLabels(
            [
                "Игрок",
                "Было место",
                "Станет место",
                "Изм. места",
                "Было очков",
                "Станет очков",
                "Изм. очков",
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

    def _build_league_group(self, league_preview: LeagueTransferPreview | None) -> QGroupBox:
        preview = league_preview or LeagueTransferPreview(available=False, reason="Предпросмотр недоступен.", rows=[])
        group = QGroupBox("Предпросмотр переходов между лигами", self)
        layout = QVBoxLayout(group)

        self.league_status_label = QLabel(group)
        self.league_status_label.setWordWrap(True)
        if preview.available:
            if preview.rows:
                self.league_status_label.setText(
                    "Показаны игроки, у которых после публикации изменится лига."
                )
            else:
                self.league_status_label.setText("После публикации переходов между лигами не появится.")
        else:
            self.league_status_label.setText(preview.reason or "Предпросмотр недоступен.")
        layout.addWidget(self.league_status_label)

        self.league_table = QTableWidget(0, 3, group)
        self.league_table.setHorizontalHeaderLabels(["Игрок", "Из лиги", "В лигу"])
        self.league_table.verticalHeader().setVisible(False)
        self.league_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.league_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.league_table.setAlternatingRowColors(True)
        header = self.league_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in range(1, self.league_table.columnCount()):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)

        for preview_row in preview.rows:
            row_index = self.league_table.rowCount()
            self.league_table.insertRow(row_index)
            values = [preview_row.fio, preview_row.from_league_code or "", preview_row.to_league_code]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if column == 0:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.league_table.setItem(row_index, column, item)

        layout.addWidget(self.league_table)
        return group

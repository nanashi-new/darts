from __future__ import annotations

import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from app.services.import_report import (
    ImportSessionReport,
    ImportSessionReportRecord,
    list_import_reports,
    render_import_report_json,
    render_import_report_text,
)
from app.ui.labels import import_apply_status_label


class ImportReportsDialog(QDialog):
    def __init__(self, *, connection: sqlite3.Connection, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("История импортов")
        self.resize(900, 620)

        self._connection = connection
        self._records: list[ImportSessionReportRecord] = list_import_reports(connection)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Сохраненные отчеты по сессиям импорта.", self))

        content_layout = QHBoxLayout()
        self.report_list = QListWidget(self)
        self.report_list.currentRowChanged.connect(self._sync_selected_report)
        content_layout.addWidget(self.report_list, 2)

        self.details_text = QTextEdit(self)
        self.details_text.setReadOnly(True)
        content_layout.addWidget(self.details_text, 3)
        layout.addLayout(content_layout)

        actions_layout = QHBoxLayout()
        self.export_txt_button = QPushButton("Экспорт TXT", self)
        self.export_txt_button.clicked.connect(self._export_selected_txt)
        actions_layout.addWidget(self.export_txt_button)

        self.export_json_button = QPushButton("Экспорт JSON", self)
        self.export_json_button.clicked.connect(self._export_selected_json)
        actions_layout.addWidget(self.export_json_button)
        actions_layout.addStretch(1)
        layout.addLayout(actions_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        if close_button := button_box.button(QDialogButtonBox.StandardButton.Close):
            close_button.setText("Закрыть")
        button_box.rejected.connect(self.reject)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        self._populate_reports()
        self._sync_selected_report()

    def _populate_reports(self) -> None:
        self.report_list.clear()
        for record in self._records:
            report = record.report
            text = (
                f"{record.created_at} | {report.tournament_name} | {import_apply_status_label(report.apply_status)} | "
                f"импортировано={report.rows_imported} пропущено={report.rows_skipped} | "
                f"предупреждений={report.warnings_count}"
            )
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, record.audit_event_id)
            self.report_list.addItem(item)
        if self._records:
            self.report_list.setCurrentRow(0)

    def _selected_record(self) -> ImportSessionReportRecord | None:
        row = self.report_list.currentRow()
        if row < 0 or row >= len(self._records):
            return None
        return self._records[row]

    def _sync_selected_report(self, _row: int | None = None) -> None:
        record = self._selected_record()
        enabled = record is not None
        self.export_txt_button.setEnabled(enabled)
        self.export_json_button.setEnabled(enabled)
        if record is None:
            self.details_text.clear()
            return
        self.details_text.setPlainText(render_import_report_text(record.report))

    def _export_selected_txt(self) -> None:
        record = self._selected_record()
        if record is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт отчета импорта в TXT",
            self._default_export_name(record.report, ".txt"),
            "Текстовые файлы (*.txt)",
        )
        if not path:
            return
        Path(path).write_text(render_import_report_text(record.report), encoding="utf-8")
        QMessageBox.information(self, "История импортов", f"TXT экспортирован: {path}")

    def _export_selected_json(self) -> None:
        record = self._selected_record()
        if record is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт отчета импорта в JSON",
            self._default_export_name(record.report, ".json"),
            "Файлы JSON (*.json)",
        )
        if not path:
            return
        Path(path).write_text(render_import_report_json(record.report), encoding="utf-8")
        QMessageBox.information(self, "История импортов", f"JSON экспортирован: {path}")

    @staticmethod
    def _default_export_name(report: ImportSessionReport, suffix: str) -> str:
        safe_name = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in report.tournament_name)
        safe_name = safe_name.strip("_") or "otchet-importa"
        return f"{safe_name}-{report.apply_status}{suffix}"

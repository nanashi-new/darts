from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.db.database import get_connection
from app.services.audit_log import AuditLogService, EXPORT_BATCH, RECALC_ALL
from app.services.batch_export import BatchExportService
from app.services.recalculate_tournament import recalculate_all_tournaments
from app.ui.audit_log_dialog import AuditLogDialog


class ReportsView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._connection = get_connection()
        self._batch_export_service = BatchExportService(self._connection)
        self._audit_log_service = AuditLogService(self._connection)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Раздел «Отчёты»."))

        self._batch_format_combo = QComboBox(self)
        self._batch_format_combo.addItems(["PDF", "XLSX", "PNG"])
        layout.addWidget(QLabel("Формат пакетного экспорта:"))
        layout.addWidget(self._batch_format_combo)

        batch_export_btn = QPushButton("Экспорт в папку", self)
        batch_export_btn.clicked.connect(self._export_batch)
        layout.addWidget(batch_export_btn)

        recalc_btn = QPushButton("Пересчитать всё", self)
        recalc_btn.clicked.connect(self._recalculate_all)
        layout.addWidget(recalc_btn)

        journal_btn = QPushButton("Журнал", self)
        journal_btn.clicked.connect(self._open_journal)
        layout.addWidget(journal_btn)
        layout.addStretch(1)

    def _export_batch(self) -> None:
        base_directory = QFileDialog.getExistingDirectory(self, "Выберите папку для экспорта")
        if not base_directory:
            QMessageBox.warning(self, "Пакетный экспорт", "Папка для экспорта не выбрана.")
            return

        export_format = self._batch_format_combo.currentText().lower()
        try:
            result = self._batch_export_service.export_all(base_directory, export_format=export_format)
        except (OSError, ValueError) as exc:
            self._audit_log_service.log_event(
                EXPORT_BATCH,
                "Ошибка пакетного экспорта",
                str(exc),
                level="error",
                context={"base_directory": base_directory, "format": export_format},
            )
            QMessageBox.critical(self, "Пакетный экспорт", str(exc))
            return

        self._audit_log_service.log_event(
            EXPORT_BATCH,
            "Пакетный экспорт завершён",
            f"Создано файлов: {len(result.files_created)}; папка: {result.run_directory}",
            context={"base_directory": base_directory, "format": export_format},
        )

        QMessageBox.information(
            self,
            "Пакетный экспорт",
            f"Готово. Папка: {result.run_directory}\nФайлов: {len(result.files_created)}",
        )

    def _recalculate_all(self) -> None:
        report = recalculate_all_tournaments(connection=self._connection)
        self._audit_log_service.log_event(
            RECALC_ALL,
            "Пересчёт всех турниров",
            (
                f"Турниров: {report.tournaments_processed}; "
                f"обновлено: {report.results_updated}; "
                f"warnings: {len(report.warnings)}; errors: {len(report.errors)}"
            ),
            level="error" if report.errors else "warning" if report.warnings else "info",
        )
        QMessageBox.information(
            self,
            "Пересчитать всё",
            (
                f"Турниров: {report.tournaments_processed}\n"
                f"Обновлено результатов: {report.results_updated}\n"
                f"Warnings: {len(report.warnings)}\n"
                f"Errors: {len(report.errors)}"
            ),
        )

    def _open_journal(self) -> None:
        dialog = AuditLogDialog(self._audit_log_service, self)
        dialog.exec()

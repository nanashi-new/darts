from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.db.database import get_connection
from app.services.audit_log import AuditLogService, EXPORT_BATCH, RECALC_ALL
from app.services.batch_export import BatchExportService
from app.services.recalculate_tournament import recalculate_all_tournaments
from app.ui.audit_log_dialog import AuditLogDialog
from app.ui.import_reports_dialog import ImportReportsDialog


class ReportsView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._connection = get_connection()
        self._batch_export_service = BatchExportService(self._connection)
        self._audit_log_service = AuditLogService(self._connection)
        layout = QVBoxLayout(self)
        scroll_area = QScrollArea(self)
        scroll_area.setObjectName("reports_scroll_area")
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        content = QWidget(self)
        scroll_area.setWidget(content)
        content_layout = QVBoxLayout(content)
        title = QLabel("Отчеты и служебные операции", content)
        title.setWordWrap(True)
        content_layout.addWidget(title)

        self._batch_format_combo = QComboBox(self)
        self._batch_format_combo.addItems(["PDF", "XLSX", "PNG"])
        content_layout.addWidget(QLabel("Формат пакетного экспорта:"))
        content_layout.addWidget(self._batch_format_combo)

        actions = QHBoxLayout()
        batch_export_btn = QPushButton("Экспорт", content)
        batch_export_btn.setToolTip("Выгрузить рейтинги и протоколы в выбранную папку.")
        batch_export_btn.clicked.connect(self._export_batch)
        actions.addWidget(batch_export_btn)

        recalc_btn = QPushButton("Пересчет", content)
        recalc_btn.setToolTip("Пересчитать результаты всех турниров.")
        recalc_btn.clicked.connect(self._recalculate_all)
        actions.addWidget(recalc_btn)

        journal_btn = QPushButton("Журнал", content)
        journal_btn.setToolTip("Открыть журнал действий и ошибок.")
        journal_btn.clicked.connect(self._open_journal)
        actions.addWidget(journal_btn)

        import_history_btn = QPushButton("Импорты", content)
        import_history_btn.setToolTip("Открыть историю импортов.")
        import_history_btn.clicked.connect(self._open_import_history)
        actions.addWidget(import_history_btn)
        actions.addStretch(1)
        content_layout.addLayout(actions)
        hint = QLabel(
            "Пакетный экспорт создает рейтинги и протоколы в выбранной папке. "
            "Пересчет используйте перед финальной проверкой данных.",
            content,
        )
        hint.setWordWrap(True)
        content_layout.addWidget(hint)
        content_layout.addStretch(1)

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
                f"предупреждений: {len(report.warnings)}; ошибок: {len(report.errors)}"
            ),
            level="error" if report.errors else "warning" if report.warnings else "info",
        )
        QMessageBox.information(
            self,
            "Пересчитать всё",
            (
                f"Турниров: {report.tournaments_processed}\n"
                f"Обновлено результатов: {report.results_updated}\n"
                f"Предупреждений: {len(report.warnings)}\n"
                f"Ошибок: {len(report.errors)}"
            ),
        )

    def _open_journal(self) -> None:
        dialog = AuditLogDialog(self._audit_log_service, self)
        dialog.exec()

    def _open_import_history(self) -> None:
        dialog = ImportReportsDialog(connection=self._connection, parent=self)
        dialog.exec()

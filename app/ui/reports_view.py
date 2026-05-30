from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.db.database import get_connection
from app.db.repositories import ReportTemplateRepository, TournamentRepository
from app.services.audit_log import AuditLogService, EXPORT_BATCH, RECALC_ALL
from app.services.batch_export import BatchExportService
from app.services.recalculate_tournament import recalculate_all_tournaments
from app.services.report_builder import ReportBuilderService, ReportConfig
from app.ui.audit_log_dialog import AuditLogDialog
from app.ui.import_reports_dialog import ImportReportsDialog
from app.ui.report_constructor_dialog import ReportConstructorDialog


class ReportsView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._connection = get_connection()
        self._batch_export_service = BatchExportService(self._connection)
        self._audit_log_service = AuditLogService(self._connection)
        self._report_builder = ReportBuilderService()
        self._template_repo = ReportTemplateRepository(self._connection)
        self._tournament_repo = TournamentRepository(self._connection)
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

        constructor_btn = QPushButton("Конструктор отчетов", content)
        constructor_btn.setToolTip("Открыть конструктор настраиваемых отчетов.")
        constructor_btn.clicked.connect(self._open_constructor)
        actions.addWidget(constructor_btn)

        actions.addStretch(1)
        content_layout.addLayout(actions)
        hint = QLabel(
            "Пакетный экспорт создает рейтинги и протоколы в выбранной папке. "
            "Пересчет используйте перед финальной проверкой данных.",
            content,
        )
        hint.setWordWrap(True)
        content_layout.addWidget(hint)

        templates_group = QGroupBox("Шаблоны отчетов", content)
        templates_layout = QVBoxLayout(templates_group)
        self._templates_list = QListWidget()
        templates_layout.addWidget(self._templates_list)
        templates_btn_layout = QHBoxLayout()
        load_btn = QPushButton("Загрузить шаблон")
        load_btn.setToolTip("Открыть конструктор с настройками выбранного шаблона.")
        load_btn.clicked.connect(self._load_template)
        templates_btn_layout.addWidget(load_btn)
        delete_btn = QPushButton("Удалить шаблон")
        delete_btn.setToolTip("Удалить выбранный шаблон.")
        delete_btn.clicked.connect(self._delete_template)
        templates_btn_layout.addWidget(delete_btn)
        templates_btn_layout.addStretch(1)
        templates_layout.addLayout(templates_btn_layout)
        content_layout.addWidget(templates_group)

        content_layout.addStretch(1)
        self._refresh_templates()

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

    def _open_constructor(self) -> None:
        leagues = self._tournament_repo.list_league_codes()
        categories = self._tournament_repo.list_category_codes()
        dialog = ReportConstructorDialog(leagues, categories, self)
        if dialog.exec():
            config = dialog.get_config()
            if dialog.save_requested:
                self._save_template_from_config(config)
            elif dialog.build_accepted:
                self._build_report(config)

    def _build_report(self, config: ReportConfig) -> None:
        output_dir = QFileDialog.getExistingDirectory(self, "Выберите папку для отчета")
        if not output_dir:
            return
        try:
            result = self._report_builder.build_report(self._connection, config, output_dir)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Конструктор отчетов", str(exc))
            return
        QMessageBox.information(
            self,
            "Конструктор отчетов",
            f"Отчет создан: {result.file_path}\nРазделов: {len(result.sections_generated)}\nСтрок: {result.total_rows}",
        )

    def _save_template_from_config(self, config: ReportConfig) -> None:
        name, ok = QInputDialog.getText(self, "Сохранить шаблон", "Название шаблона:")
        if not ok or not name.strip():
            return
        self._template_repo.save_template(name.strip(), config.to_json())
        self._refresh_templates()

    def _refresh_templates(self) -> None:
        self._templates_list.clear()
        self._template_rows = self._template_repo.list_templates()
        for row in self._template_rows:
            self._templates_list.addItem(f"{row['name']} ({row['created_at']})")

    def _load_template(self) -> None:
        idx = self._templates_list.currentRow()
        if idx < 0 or idx >= len(self._template_rows):
            QMessageBox.warning(self, "Шаблоны", "Выберите шаблон из списка.")
            return
        row = self._template_rows[idx]
        config = ReportConfig.from_json(row["config_json"])
        leagues = self._tournament_repo.list_league_codes()
        categories = self._tournament_repo.list_category_codes()
        dialog = ReportConstructorDialog(leagues, categories, self)
        dialog.load_config(config)
        if dialog.exec():
            new_config = dialog.get_config()
            if dialog.save_requested:
                self._save_template_from_config(new_config)
            elif dialog.build_accepted:
                self._build_report(new_config)

    def _delete_template(self) -> None:
        idx = self._templates_list.currentRow()
        if idx < 0 or idx >= len(self._template_rows):
            QMessageBox.warning(self, "Шаблоны", "Выберите шаблон из списка.")
            return
        row = self._template_rows[idx]
        self._template_repo.delete_template(row["id"])
        self._refresh_templates()

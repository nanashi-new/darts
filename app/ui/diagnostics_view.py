from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app import __build_metadata__
from app.db.database import get_connection
from app.runtime_paths import get_runtime_paths
from app.services.backup_restore import export_profile_backup, import_profile_from_backup, run_health_check
from app.services.diagnostics import export_diagnostic_bundle, format_self_check_summary, run_self_check
from app.services.restore_points import (
    RestorePointRecord,
    create_restore_point,
    list_restore_points,
    queue_restore_from_point,
    queue_safe_profile_reset,
)
from app.ui.labels import level_label
from app.ui.restore_point_details_dialog import RestorePointDetailsDialog


class DiagnosticsView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._connection = get_connection()
        self._paths = get_runtime_paths()
        self._restore_point_records: list[RestorePointRecord] = []
        self._build_ui()
        self._refresh_restore_points()
        self._run_self_check()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        root_layout.addWidget(scroll_area)

        content = QWidget(self)
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        scroll_area.setWidget(content)

        layout = QVBoxLayout(content)

        layout.addWidget(QLabel("Диагностика и восстановление", self))
        layout.addWidget(
            QLabel(
                (
                    f"Версия: {__build_metadata__.version} | "
                    f"Сборка: {__build_metadata__.packaging_mode} | "
                    f"Ревизия: {__build_metadata__.git_revision} | "
                    f"Схема: {__build_metadata__.schema_version}"
                ),
                self,
            )
        )
        layout.addWidget(
            QLabel(
                (
                    f"Профиль: {self._paths.profile_root}\n"
                    f"База данных: {self._paths.db_path}\n"
                    f"Настройки: {self._paths.settings_path}"
                ),
                self,
            )
        )

        self.self_check_summary = QLabel("Самопроверка: еще не запускалась", self)
        layout.addWidget(self.self_check_summary)

        self.self_check_output = QPlainTextEdit(self)
        self.self_check_output.setReadOnly(True)
        self.self_check_output.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.self_check_output, 1)

        self.run_self_check_button = QPushButton("Самопроверка", self)
        self.run_self_check_button.setToolTip("Запустить проверку профиля, базы и окружения.")
        self.run_self_check_button.clicked.connect(self._run_self_check)
        layout.addWidget(self.run_self_check_button)

        self.export_bundle_button = QPushButton("Архив", self)
        self.export_bundle_button.setToolTip("Создать диагностический архив для поддержки.")
        self.export_bundle_button.clicked.connect(self._export_bundle)
        layout.addWidget(self.export_bundle_button)

        self.open_logs_button = QPushButton("Логи", self)
        self.open_logs_button.setToolTip("Открыть папку с журналами приложения.")
        self.open_logs_button.clicked.connect(lambda: self._open_folder(self._paths.logs_dir))
        layout.addWidget(self.open_logs_button)

        self.open_profile_button = QPushButton("Профиль", self)
        self.open_profile_button.setToolTip("Открыть папку текущего профиля.")
        self.open_profile_button.clicked.connect(lambda: self._open_folder(self._paths.profile_root))
        layout.addWidget(self.open_profile_button)

        self.export_backup_button = QPushButton("Экспорт профиля", self)
        self.export_backup_button.setToolTip("Сохранить копию базы данных в выбранное место.")
        self.export_backup_button.clicked.connect(self._export_backup)
        layout.addWidget(self.export_backup_button)

        self.import_backup_button = QPushButton("Импорт профиля", self)
        self.import_backup_button.setToolTip("Восстановить профиль из ранее сохраненной копии.")
        self.import_backup_button.clicked.connect(self._import_backup)
        layout.addWidget(self.import_backup_button)

        self.health_check_button = QPushButton("Проверка здоровья", self)
        self.health_check_button.setToolTip("Проверить целостность, размер и состояние профиля.")
        self.health_check_button.clicked.connect(self._run_health_check)
        layout.addWidget(self.health_check_button)

        self.create_restore_point_button = QPushButton("Создать точку", self)
        self.create_restore_point_button.setToolTip("Создать точку восстановления профиля.")
        self.create_restore_point_button.clicked.connect(self._create_restore_point)
        layout.addWidget(self.create_restore_point_button)

        layout.addWidget(QLabel("Точки восстановления", self))
        self.restore_points_list = QListWidget(self)
        self.restore_points_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.restore_points_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.restore_points_list.itemDoubleClicked.connect(lambda *_args: self._open_selected_restore_point_details())
        layout.addWidget(self.restore_points_list, 1)

        self.restore_details_button = QPushButton("Детали", self)
        self.restore_details_button.setToolTip("Открыть детали выбранной точки восстановления.")
        self.restore_details_button.clicked.connect(self._open_selected_restore_point_details)
        layout.addWidget(self.restore_details_button)

        self.restore_selected_button = QPushButton("Восстановить", self)
        self.restore_selected_button.setToolTip("Запланировать восстановление из выбранной точки.")
        self.restore_selected_button.clicked.connect(self._restore_selected)
        layout.addWidget(self.restore_selected_button)

        self.safe_reset_button = QPushButton("Сброс", self)
        self.safe_reset_button.setToolTip("Запланировать безопасный сброс профиля.")
        self.safe_reset_button.clicked.connect(self._safe_reset)
        layout.addWidget(self.safe_reset_button)

        layout.addStretch(1)

    def _run_self_check(self) -> None:
        report = run_self_check(connection=self._connection)
        self.self_check_summary.setText(format_self_check_summary(report))
        lines = [f"Создано: {report.created_at}", f"Ошибок нет: {'да' if report.ok else 'нет'}", ""]
        if report.issues:
            for issue in report.issues:
                lines.append(f"[{level_label(issue.severity)}] {issue.code}: {issue.message}")
        else:
            lines.append("Проблем не обнаружено.")
        self.self_check_output.setPlainText("\n".join(lines))

    def _export_bundle(self) -> None:
        result = export_diagnostic_bundle(connection=self._connection)
        QMessageBox.information(
            self,
            "Диагностика",
            f"Диагностический архив создан:\n{result.bundle_path}",
        )

    def _open_folder(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _create_restore_point(self) -> None:
        record = create_restore_point(
            connection=self._connection,
            title="Ручная точка восстановления",
            reason="manual",
            source="diagnostics_view",
        )
        self._refresh_restore_points()
        QMessageBox.information(
            self,
            "Диагностика",
            f"Точка восстановления создана:\n{record.file_path}",
        )

    def _refresh_restore_points(self) -> None:
        self.restore_points_list.clear()
        self._restore_point_records = list_restore_points(connection=self._connection)
        for record in self._restore_point_records:
            item = QListWidgetItem(
                f"{record.created_at} | {record.title} | {Path(record.file_path).name}",
                self.restore_points_list,
            )
            item.setData(Qt.ItemDataRole.UserRole, record.id)
        self.restore_details_button.setEnabled(bool(self._restore_point_records))

    def _selected_restore_point_record(self) -> RestorePointRecord | None:
        item = self.restore_points_list.currentItem()
        if item is None:
            return None
        restore_point_id = int(item.data(Qt.ItemDataRole.UserRole))
        for record in self._restore_point_records:
            if record.id == restore_point_id:
                return record
        return None

    def _open_selected_restore_point_details(self) -> None:
        record = self._selected_restore_point_record()
        if record is None:
            QMessageBox.warning(self, "Диагностика", "Выберите точку восстановления.")
            return
        RestorePointDetailsDialog(record=record, parent=self).exec()

    def _restore_selected(self) -> None:
        record = self._selected_restore_point_record()
        if record is None:
            QMessageBox.warning(self, "Диагностика", "Выберите точку восстановления.")
            return
        reply = QMessageBox.warning(
            self,
            "Подтверждение",
            "Вы уверены? Текущие данные будут заменены данными из точки восстановления. Это действие необратимо.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        queue_restore_from_point(
            connection=self._connection,
            restore_point_id=record.id,
            source="diagnostics_view",
        )
        QMessageBox.information(
            self,
            "Диагностика",
            "Восстановление запланировано. Перезапустите приложение.",
        )

    def _safe_reset(self) -> None:
        reply = QMessageBox.warning(
            self,
            "Подтверждение",
            "Вы уверены? Все данные профиля будут сброшены. Резервная копия будет создана автоматически.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        queue_safe_profile_reset(
            connection=self._connection,
            source="diagnostics_view",
        )
        QMessageBox.information(
            self,
            "Диагностика",
            "Сброс профиля запланирован. Перезапустите приложение.",
        )

    def _export_backup(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт профиля",
            str(self._paths.exports_dir / "profile_backup.db"),
            "SQLite DB (*.db)",
        )
        if not file_path:
            return
        result = export_profile_backup(
            connection=self._connection,
            destination_path=Path(file_path),
        )
        QMessageBox.information(
            self,
            "Диагностика",
            f"Профиль экспортирован:\n{result.destination_path}\nРазмер: {result.size_bytes} байт",
        )

    def _import_backup(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Импорт профиля",
            "",
            "SQLite DB (*.db)",
        )
        if not file_path:
            return
        reply = QMessageBox.warning(
            self,
            "Подтверждение",
            "Вы уверены? Текущий профиль будет заменен данными из выбранного файла. "
            "Точка восстановления текущего состояния будет создана автоматически.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        result = import_profile_from_backup(
            connection=self._connection,
            source_path=Path(file_path),
        )
        if result.success:
            QMessageBox.information(self, "Диагностика", result.message)
        else:
            QMessageBox.warning(self, "Диагностика", result.message)

    def _run_health_check(self) -> None:
        result = run_health_check(connection=self._connection)
        integrity_text = "ОК" if result.integrity_ok else result.integrity_message
        size_mb = result.db_size_bytes / (1024 * 1024)
        last_backup = result.last_backup_date or "нет"
        lines = [
            f"Целостность: {integrity_text}",
            f"Размер базы: {size_mb:.2f} МБ",
            f"Последний бэкап: {last_backup}",
            f"Точек восстановления: {result.restore_points_count}",
        ]
        self.self_check_output.setPlainText("\n".join(lines))

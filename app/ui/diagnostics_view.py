from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app import __build_metadata__
from app.db.database import get_connection
from app.runtime_paths import get_runtime_paths
from app.services.diagnostics import export_diagnostic_bundle, format_self_check_summary, run_self_check
from app.services.restore_points import (
    create_restore_point,
    list_restore_points,
    queue_restore_from_point,
    queue_safe_profile_reset,
)


class DiagnosticsView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._connection = get_connection()
        self._paths = get_runtime_paths()
        self._build_ui()
        self._refresh_restore_points()
        self._run_self_check()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Диагностика и восстановление", self))
        layout.addWidget(
            QLabel(
                (
                    f"Version: {__build_metadata__.version} | "
                    f"Build: {__build_metadata__.packaging_mode} | "
                    f"Revision: {__build_metadata__.git_revision} | "
                    f"Schema: {__build_metadata__.schema_version}"
                ),
                self,
            )
        )
        layout.addWidget(
            QLabel(
                f"Profile: {self._paths.profile_root}\nDB: {self._paths.db_path}\nSettings: {self._paths.settings_path}",
                self,
            )
        )

        self.self_check_summary = QLabel("Self-check: not run", self)
        layout.addWidget(self.self_check_summary)

        self.self_check_output = QPlainTextEdit(self)
        self.self_check_output.setReadOnly(True)
        layout.addWidget(self.self_check_output)

        self.run_self_check_button = QPushButton("Запустить self-check", self)
        self.run_self_check_button.clicked.connect(self._run_self_check)
        layout.addWidget(self.run_self_check_button)

        self.export_bundle_button = QPushButton("Экспорт diagnostic bundle", self)
        self.export_bundle_button.clicked.connect(self._export_bundle)
        layout.addWidget(self.export_bundle_button)

        self.open_logs_button = QPushButton("Открыть папку логов", self)
        self.open_logs_button.clicked.connect(lambda: self._open_folder(self._paths.logs_dir))
        layout.addWidget(self.open_logs_button)

        self.open_profile_button = QPushButton("Открыть профиль", self)
        self.open_profile_button.clicked.connect(lambda: self._open_folder(self._paths.profile_root))
        layout.addWidget(self.open_profile_button)

        self.create_restore_point_button = QPushButton("Создать restore point", self)
        self.create_restore_point_button.clicked.connect(self._create_restore_point)
        layout.addWidget(self.create_restore_point_button)

        layout.addWidget(QLabel("Restore points", self))
        self.restore_points_list = QListWidget(self)
        self.restore_points_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.restore_points_list)

        self.restore_selected_button = QPushButton("Восстановить выбранный point", self)
        self.restore_selected_button.clicked.connect(self._restore_selected)
        layout.addWidget(self.restore_selected_button)

        self.safe_reset_button = QPushButton("Безопасный reset профиля", self)
        self.safe_reset_button.clicked.connect(self._safe_reset)
        layout.addWidget(self.safe_reset_button)

        layout.addStretch(1)

    def _run_self_check(self) -> None:
        report = run_self_check(connection=self._connection)
        self.self_check_summary.setText(format_self_check_summary(report))
        lines = [f"Created: {report.created_at}", f"OK: {report.ok}", ""]
        if report.issues:
            for issue in report.issues:
                lines.append(f"[{issue.severity}] {issue.code}: {issue.message}")
        else:
            lines.append("No issues detected.")
        self.self_check_output.setPlainText("\n".join(lines))

    def _export_bundle(self) -> None:
        result = export_diagnostic_bundle(connection=self._connection)
        QMessageBox.information(
            self,
            "Diagnostics",
            f"Diagnostic bundle создан:\n{result.bundle_path}",
        )

    def _open_folder(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _create_restore_point(self) -> None:
        record = create_restore_point(
            connection=self._connection,
            title="Manual restore point",
            reason="manual",
            source="diagnostics_view",
        )
        self._refresh_restore_points()
        QMessageBox.information(
            self,
            "Diagnostics",
            f"Restore point создан:\n{record.file_path}",
        )

    def _refresh_restore_points(self) -> None:
        self.restore_points_list.clear()
        for record in list_restore_points(connection=self._connection):
            item = QListWidgetItem(
                f"{record.created_at} | {record.title} | {Path(record.file_path).name}",
                self.restore_points_list,
            )
            item.setData(Qt.ItemDataRole.UserRole, record.id)

    def _restore_selected(self) -> None:
        item = self.restore_points_list.currentItem()
        if item is None:
            QMessageBox.warning(self, "Diagnostics", "Выберите restore point.")
            return
        restore_point_id = int(item.data(Qt.ItemDataRole.UserRole))
        queue_restore_from_point(
            connection=self._connection,
            restore_point_id=restore_point_id,
            source="diagnostics_view",
        )
        QMessageBox.information(
            self,
            "Diagnostics",
            "Восстановление запланировано. Перезапустите приложение.",
        )

    def _safe_reset(self) -> None:
        queue_safe_profile_reset(
            connection=self._connection,
            source="diagnostics_view",
        )
        QMessageBox.information(
            self,
            "Diagnostics",
            "Safe reset запланирован. Перезапустите приложение.",
        )

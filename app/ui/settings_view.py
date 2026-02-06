from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from app.db.database import get_connection
from app.services.audit_log import AuditLogService, RECALC_ALL
from app.services.norms_loader import load_norms_from_settings
from app.services.recalculate_tournament import recalculate_all_tournaments
from app.settings import get_norms_xlsx_path, set_norms_xlsx_path


class SettingsView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._connection = get_connection()
        self._audit_log_service = AuditLogService(self._connection)
        self._build_ui()
        self._refresh_norms_info()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Путь к norms.xlsx"))
        path_layout = QHBoxLayout()
        self.norms_path_edit = QLineEdit(get_norms_xlsx_path(), self)
        browse_btn = QPushButton("Выбрать файл", self)
        browse_btn.clicked.connect(self._pick_norms_file)
        save_btn = QPushButton("Сохранить", self)
        save_btn.clicked.connect(self._save_norms_path)
        path_layout.addWidget(self.norms_path_edit)
        path_layout.addWidget(browse_btn)
        path_layout.addWidget(save_btn)
        layout.addLayout(path_layout)

        open_folder_btn = QPushButton("Открыть папку нормативов", self)
        open_folder_btn.clicked.connect(self._open_norms_folder)
        layout.addWidget(open_folder_btn)

        self.norms_info_label = QLabel("Версия/дата нормативов: —", self)
        layout.addWidget(self.norms_info_label)

        recalc_all_btn = QPushButton("Пересчитать всё", self)
        recalc_all_btn.clicked.connect(self._recalculate_all)
        layout.addWidget(recalc_all_btn)

        layout.addStretch(1)

    def _pick_norms_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл нормативов",
            self.norms_path_edit.text().strip(),
            "Excel Files (*.xlsx)",
        )
        if path:
            self.norms_path_edit.setText(path)

    def _save_norms_path(self) -> None:
        path = self.norms_path_edit.text().strip()
        if not path:
            QMessageBox.warning(self, "Настройки", "Укажите путь к файлу нормативов.")
            return
        set_norms_xlsx_path(path)
        self._refresh_norms_info()
        QMessageBox.information(self, "Настройки", "Путь к нормативам сохранён.")

    def _open_norms_folder(self) -> None:
        folder = str(Path(self.norms_path_edit.text().strip() or get_norms_xlsx_path()).parent)
        if not os.path.isdir(folder):
            QMessageBox.warning(self, "Настройки", "Папка нормативов не найдена.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def _refresh_norms_info(self) -> None:
        norms_load = load_norms_from_settings()
        if not norms_load.loaded:
            self.norms_info_label.setText(f"Нормативы: ошибка ({norms_load.warning})")
            return

        version = norms_load.version or "—"
        updated_at = norms_load.updated_at or "—"
        self.norms_info_label.setText(
            f"Нормативы: OK | версия: {version} | дата: {updated_at}"
        )

    def _recalculate_all(self) -> None:
        report = recalculate_all_tournaments(connection=self._connection)
        self._audit_log_service.log_event(
            RECALC_ALL,
            "Пересчёт всех турниров (настройки)",
            (
                f"Турниров: {report.tournaments_processed}; "
                f"обновлено: {report.results_updated}; "
                f"warnings: {len(report.warnings)}; errors: {len(report.errors)}"
            ),
            level="error" if report.errors else "warning" if report.warnings else "info",
        )
        details = [
            f"Турниров: {report.tournaments_processed}",
            f"Обновлено результатов: {report.results_updated}",
            f"Warnings: {len(report.warnings)}",
            f"Errors: {len(report.errors)}",
        ]
        if report.warnings:
            details.append("\n".join(report.warnings[:3]))
        if report.errors:
            details.append("\n".join(report.errors[:3]))
        QMessageBox.information(self, "Пересчитать всё", "\n".join(details))

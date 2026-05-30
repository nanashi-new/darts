"""Attachments widget for entity file management."""
from __future__ import annotations

import os
import shutil
import sqlite3

from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.runtime_paths import get_runtime_paths
from app.services.attachments import (
    AttachmentRecord,
    create_attachment,
    delete_attachment,
    list_entity_attachments,
)


class AttachmentsWidget(QWidget):
    """Reusable widget for displaying and managing attachments on an entity."""

    def __init__(
        self,
        *,
        connection: sqlite3.Connection,
        entity_type: str,
        entity_id: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._connection = connection
        self._entity_type = entity_type
        self._entity_id = entity_id
        self._attachments: list[AttachmentRecord] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Table
        self._table = QTableWidget(0, 4, self)
        self._table.setHorizontalHeaderLabels(["Файл", "Описание", "Размер", "Дата"])
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        header = self._table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(True)
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self._table)

        # Buttons row
        btn_row = QHBoxLayout()
        self._attach_button = QPushButton("Прикрепить")
        self._attach_button.clicked.connect(self._on_attach)
        btn_row.addWidget(self._attach_button)

        self._delete_button = QPushButton("Удалить")
        self._delete_button.clicked.connect(self._on_delete)
        btn_row.addWidget(self._delete_button)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        self._refresh()

    def _refresh(self) -> None:
        self._attachments = list_entity_attachments(self._connection, self._entity_type, self._entity_id)
        self._table.setRowCount(0)
        for att in self._attachments:
            row_index = self._table.rowCount()
            self._table.insertRow(row_index)
            self._table.setItem(row_index, 0, QTableWidgetItem(att.file_name))
            self._table.setItem(row_index, 1, QTableWidgetItem(att.description or ""))
            size_str = self._format_size(att.file_size) if att.file_size else ""
            self._table.setItem(row_index, 2, QTableWidgetItem(size_str))
            self._table.setItem(row_index, 3, QTableWidgetItem(att.created_at[:19]))

    def _on_attach(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Выбрать файл")
        if not file_path:
            return

        file_name = os.path.basename(file_path)
        try:
            file_size = os.path.getsize(file_path)
        except OSError:
            file_size = None

        # Copy file into profile attachments directory
        profile_root = get_runtime_paths().profile_root
        dest_dir = profile_root / "attachments" / self._entity_type / self._entity_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / file_name
        try:
            shutil.copy2(file_path, dest_path)
        except OSError:
            QMessageBox.warning(self, "Ошибка", "Не удалось скопировать файл.")
            return

        # Store path relative to profile_root
        relative_path = str(dest_path.relative_to(profile_root))

        create_attachment(
            self._connection,
            self._entity_type,
            self._entity_id,
            relative_path,
            file_name,
            description=None,
            file_size=file_size,
        )
        self._refresh()

    def _on_delete(self) -> None:
        row = self._table.currentRow()
        if row < 0 or row >= len(self._attachments):
            return
        att = self._attachments[row]
        reply = QMessageBox.question(
            self,
            "Удалить вложение",
            f"Удалить вложение '{att.file_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_attachment(self._connection, att.id)
            self._refresh()

    @staticmethod
    def _format_size(size: int) -> str:
        if size < 1024:
            return f"{size} Б"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} КБ"
        return f"{size / (1024 * 1024):.1f} МБ"

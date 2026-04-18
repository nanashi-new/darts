from __future__ import annotations

import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.services.rating_snapshot import (
    RatingSnapshotEntry,
    RatingSnapshotSession,
    list_rating_snapshot_rows,
    list_rating_snapshot_sessions,
)


class RatingHistoryDialog(QDialog):
    def __init__(self, *, connection: sqlite3.Connection, scope_type: str, scope_key: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("История рейтинга")
        self.resize(960, 620)

        self._connection = connection
        self._scope_type = scope_type
        self._scope_key = scope_key
        self._sessions = list_rating_snapshot_sessions(connection, scope_type=scope_type, scope_key=scope_key)
        self._rows: list[RatingSnapshotEntry] = []

        layout = QVBoxLayout(self)
        self.status_label = QLabel(self)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        content_layout = QHBoxLayout()

        self.session_list = QListWidget(self)
        self.session_list.currentRowChanged.connect(self._sync_selected_session)
        content_layout.addWidget(self.session_list, 2)

        self.rows_table = QTableWidget(0, 4, self)
        self.rows_table.setHorizontalHeaderLabels(["Место", "Игрок", "Очки", "Учтено турниров"])
        self.rows_table.verticalHeader().setVisible(False)
        self.rows_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.rows_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.rows_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.rows_table.itemSelectionChanged.connect(self._sync_selected_row)
        content_layout.addWidget(self.rows_table, 4)

        self.basis_list = QListWidget(self)
        content_layout.addWidget(self.basis_list, 3)
        layout.addLayout(content_layout)

        self._populate_sessions()
        self._sync_selected_session()

    def _populate_sessions(self) -> None:
        self.session_list.clear()
        for session in self._sessions:
            item = QListWidgetItem(
                (
                    f"{session.created_at} | {session.scope_key} | "
                    f"source tournament={session.source_tournament_id} | entries={session.entries_count}"
                )
            )
            self.session_list.addItem(item)
        if self._sessions:
            self.session_list.setCurrentRow(0)

    def _sync_selected_session(self, _row: int | None = None) -> None:
        current_row = self.session_list.currentRow()
        if current_row < 0 or current_row >= len(self._sessions):
            self._rows = []
            self.rows_table.setRowCount(0)
            self.basis_list.clear()
            self.status_label.setText(
                f"История рейтинга для scope {self._scope_type}:{self._scope_key} пока не создана."
            )
            return

        session = self._sessions[current_row]
        self._rows = list_rating_snapshot_rows(
            self._connection,
            snapshot_created_at=session.created_at,
            scope_type=session.scope_type,
            scope_key=session.scope_key,
        )
        self.rows_table.setRowCount(0)
        for entry in self._rows:
            row_index = self.rows_table.rowCount()
            self.rows_table.insertRow(row_index)
            values = [
                str(entry.position),
                entry.fio,
                str(entry.points),
                str(entry.tournaments_count),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column != 1:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.rows_table.setItem(row_index, column, item)

        self.basis_list.clear()
        self.status_label.setText(
            (
                f"История рейтинга: scope {session.scope_type}:{session.scope_key}; "
                f"snapshots={len(self._sessions)}; rows={len(self._rows)}"
            )
        )
        if self._rows:
            self.rows_table.selectRow(0)
            self._sync_selected_row()

    def _sync_selected_row(self) -> None:
        selected_row = self.rows_table.currentRow()
        if selected_row < 0 or selected_row >= len(self._rows):
            self.basis_list.clear()
            return

        entry = self._rows[selected_row]
        self.basis_list.clear()
        for basis_item in entry.rolling_basis:
            self.basis_list.addItem(
                QListWidgetItem(
                    (
                        f"Tournament #{basis_item.tournament_id} | "
                        f"date={basis_item.tournament_date} | "
                        f"points={basis_item.points_total}"
                    )
                )
            )
        self.status_label.setText(
            (
                f"История рейтинга: scope {entry.scope_type}:{entry.scope_key}; "
                f"игрок {entry.fio}; basis={len(entry.rolling_basis)}"
            )
        )

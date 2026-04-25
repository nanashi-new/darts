from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.db.database import get_connection
from app.db.repositories import TournamentRepository
from app.services.import_report import list_import_reports
from app.services.notes import list_notes_hub
from app.settings import get_last_self_check
from app.ui.labels import import_apply_status_label, tournament_status_label, visibility_label
from app.ui.player_card_dialog import PlayerCardDialog


class DashboardView(QWidget):
    def __init__(self, *, navigate: Callable[[str], None] | None = None) -> None:
        super().__init__()
        self._connection = get_connection()
        self._navigate = navigate
        self._tournament_repo = TournamentRepository(self._connection)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Главная", self))
        layout.addLayout(self._build_quick_actions())

        self.recent_tournaments_table = QTableWidget(0, 3, self)
        self.recent_tournaments_table.setHorizontalHeaderLabels(["Дата", "Турнир", "Статус"])
        layout.addWidget(QLabel("Последние турниры", self))
        layout.addWidget(self.recent_tournaments_table)

        self.recent_imports_table = QTableWidget(0, 4, self)
        self.recent_imports_table.setHorizontalHeaderLabels(["Создан", "Турнир", "Статус", "Импортировано"])
        layout.addWidget(QLabel("Последние отчеты импорта", self))
        layout.addWidget(self.recent_imports_table)

        self.follow_up_notes_table = QTableWidget(0, 3, self)
        self.follow_up_notes_table.setHorizontalHeaderLabels(["Объект", "Заголовок", "Доступ"])
        layout.addWidget(QLabel("Контрольные заметки", self))
        layout.addWidget(self.follow_up_notes_table)

        self.open_follow_up_player_button = QPushButton("Открыть карточку выбранного игрока", self)
        self.open_follow_up_player_button.clicked.connect(self._open_selected_follow_up_player)
        layout.addWidget(self.open_follow_up_player_button)

        self.diagnostics_summary_label = QLabel("Диагностика: самопроверка еще не запускалась", self)
        layout.addWidget(self.diagnostics_summary_label)

        layout.addStretch(1)
        self.refresh()

    def _build_quick_actions(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        for label in ["Турниры", "Игроки", "Контекст", "Диагностика"]:
            button = QPushButton(label, self)
            button.clicked.connect(lambda _checked=False, target=label: self._navigate_to(target))
            layout.addWidget(button)
        layout.addStretch(1)
        return layout

    def refresh(self) -> None:
        self._fill_recent_tournaments()
        self._fill_recent_imports()
        self._fill_follow_up_notes()
        self._fill_diagnostics_summary()

    def _fill_recent_tournaments(self) -> None:
        self.recent_tournaments_table.setRowCount(0)
        for tournament in self._tournament_repo.list()[:5]:
            row_index = self.recent_tournaments_table.rowCount()
            self.recent_tournaments_table.insertRow(row_index)
            values = [
                tournament.get("date"),
                tournament.get("name"),
                tournament_status_label(tournament.get("status")),
            ]
            for column, value in enumerate(values):
                self.recent_tournaments_table.setItem(
                    row_index,
                    column,
                    QTableWidgetItem("" if value is None else str(value)),
                )

    def _fill_recent_imports(self) -> None:
        self.recent_imports_table.setRowCount(0)
        for report_record in list_import_reports(self._connection)[:5]:
            row_index = self.recent_imports_table.rowCount()
            self.recent_imports_table.insertRow(row_index)
            values = [
                report_record.created_at,
                report_record.report.tournament_name,
                import_apply_status_label(report_record.report.apply_status),
                report_record.report.rows_imported,
            ]
            for column, value in enumerate(values):
                self.recent_imports_table.setItem(row_index, column, QTableWidgetItem(str(value)))

    def _fill_follow_up_notes(self) -> None:
        self.follow_up_notes_table.setRowCount(0)
        for note in list_notes_hub(
            connection=self._connection,
            note_types=["follow_up"],
        )[:5]:
            row_index = self.follow_up_notes_table.rowCount()
            self.follow_up_notes_table.insertRow(row_index)
            values = [
                note.entity_label or f"{note.entity_type}:{note.entity_id}",
                note.title,
                visibility_label(note.visibility),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.ItemDataRole.UserRole, note.entity_type)
                item.setData(Qt.ItemDataRole.UserRole + 1, note.entity_id)
                self.follow_up_notes_table.setItem(row_index, column, item)

    def _fill_diagnostics_summary(self) -> None:
        last_self_check = get_last_self_check()
        if not last_self_check:
            self.diagnostics_summary_label.setText("Диагностика: самопроверка еще не запускалась")
            return
        issues = last_self_check.get("issues", [])
        created_at = last_self_check.get("created_at", "-")
        self.diagnostics_summary_label.setText(
            f"Диагностика: проблем - {len(issues)}, последняя проверка - {created_at}"
        )

    def _open_selected_follow_up_player(self) -> None:
        row = self.follow_up_notes_table.currentRow()
        if row < 0:
            return
        item = self.follow_up_notes_table.item(row, 0)
        if item is None:
            return
        entity_type = str(item.data(Qt.ItemDataRole.UserRole) or "")
        entity_id = str(item.data(Qt.ItemDataRole.UserRole + 1) or "")
        if entity_type == "player" and entity_id.isdigit():
            PlayerCardDialog(connection=self._connection, player_id=int(entity_id), parent=self).exec()

    def _navigate_to(self, target: str) -> None:
        if self._navigate is not None:
            self._navigate(target)

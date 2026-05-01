from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.db.database import get_connection
from app.db.repositories import TournamentRepository
from app.runtime_paths import get_runtime_paths
from app.services.import_report import list_import_reports
from app.services.notes import list_notes_hub
from app.settings import get_last_self_check
from app.ui.labels import import_apply_status_label, tournament_status_label, visibility_label
from app.ui.player_card_dialog import PlayerCardDialog


class DashboardView(QWidget):
    def __init__(self, *, navigate: Callable[[str], None] | None = None) -> None:
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._connection = get_connection()
        self._navigate = navigate
        self._tournament_repo = TournamentRepository(self._connection)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Главная", self))
        layout.addWidget(self._build_profile_status_group())
        layout.addLayout(self._build_quick_actions())
        layout.addWidget(self._build_summary_group())
        layout.addWidget(self._build_attention_group(), 1)

        self.recent_tournaments_table = QTableWidget(0, 3, self)
        self.recent_tournaments_table.setHorizontalHeaderLabels(["Дата", "Турнир", "Статус"])
        self._configure_table(self.recent_tournaments_table)
        layout.addWidget(QLabel("Последние турниры", self))
        layout.addWidget(self.recent_tournaments_table, 2)

        self.recent_imports_table = QTableWidget(0, 4, self)
        self.recent_imports_table.setHorizontalHeaderLabels(["Создан", "Турнир", "Статус", "Импортировано"])
        self._configure_table(self.recent_imports_table)
        layout.addWidget(QLabel("Последние отчеты импорта", self))
        layout.addWidget(self.recent_imports_table, 2)

        self.follow_up_notes_table = QTableWidget(0, 3, self)
        self.follow_up_notes_table.setHorizontalHeaderLabels(["Объект", "Заголовок", "Доступ"])
        self._configure_table(self.follow_up_notes_table)
        layout.addWidget(QLabel("Контрольные заметки", self))
        layout.addWidget(self.follow_up_notes_table, 2)

        self.open_follow_up_player_button = QPushButton("Карточка", self)
        self.open_follow_up_player_button.setToolTip(
            "Открыть карточку выбранного игрока из контрольных заметок."
        )
        self.open_follow_up_player_button.clicked.connect(self._open_selected_follow_up_player)
        layout.addWidget(self.open_follow_up_player_button)

        self.diagnostics_summary_label = QLabel("Диагностика: самопроверка еще не запускалась", self)
        layout.addWidget(self.diagnostics_summary_label)

        layout.addStretch(1)
        self.refresh()

    @staticmethod
    def _configure_table(table: QTableWidget) -> None:
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)

    def _build_quick_actions(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        actions = [
            ("Рейтинг", "Рейтинг", "Открыть текущие рейтинги по категориям и взрослым зачетам."),
            ("Турниры", "Турниры", "Открыть турниры, публикацию и корректировки."),
            ("Игроки", "Игроки", "Открыть список игроков и карточки."),
            ("Импорт", "Импорт/Экспорт", "Импортировать XLSX и проверить отчет перед публикацией."),
            ("Отчеты", "Отчеты", "Открыть экспорт, журнал и историю импортов."),
            ("Диагностика", "Диагностика", "Проверить профиль, логи и точки восстановления."),
        ]
        for label, target, tooltip in actions:
            button = QPushButton(label, self)
            button.setToolTip(tooltip)
            button.clicked.connect(lambda _checked=False, target=target: self._navigate_to(target))
            layout.addWidget(button)
        layout.addStretch(1)
        return layout

    def _build_profile_status_group(self) -> QGroupBox:
        group = QGroupBox("Статус рабочего профиля", self)
        layout = QGridLayout(group)
        self.profile_status_label = QLabel("Профиль: -", group)
        self.database_status_label = QLabel("База: -", group)
        self.dashboard_diagnostics_label = QLabel("Диагностика: -", group)
        self.refresh_button = QPushButton("Обновить", group)
        self.refresh_button.setToolTip("Обновить сводку главной страницы.")
        self.refresh_button.clicked.connect(self.refresh)
        layout.addWidget(self.profile_status_label, 0, 0)
        layout.addWidget(self.database_status_label, 0, 1)
        layout.addWidget(self.dashboard_diagnostics_label, 0, 2)
        layout.addWidget(self.refresh_button, 0, 3)
        return group

    def _build_summary_group(self) -> QGroupBox:
        group = QGroupBox("Операционная сводка", self)
        layout = QGridLayout(group)
        self.summary_labels: dict[str, QLabel] = {}
        entries = [
            ("players", "Игроки"),
            ("tournaments", "Турниры"),
            ("drafts", "Черновики"),
            ("review", "На проверке"),
            ("published", "Опубликованы"),
            ("follow_up", "Контрольные заметки"),
            ("restore_points", "Точки восстановления"),
        ]
        for index, (key, title) in enumerate(entries):
            label = QLabel(f"{title}: 0", group)
            self.summary_labels[key] = label
            layout.addWidget(label, index // 4, index % 4)
        return group

    def _build_attention_group(self) -> QGroupBox:
        group = QGroupBox("Требует внимания", self)
        layout = QVBoxLayout(group)
        self.attention_table = QTableWidget(0, 3, group)
        self.attention_table.setHorizontalHeaderLabels(["Приоритет", "Сценарий", "Что сделать"])
        self._configure_table(self.attention_table)
        layout.addWidget(self.attention_table)
        return group

    def refresh(self) -> None:
        self._fill_profile_status()
        self._fill_summary()
        self._fill_attention()
        self._fill_recent_tournaments()
        self._fill_recent_imports()
        self._fill_follow_up_notes()
        self._fill_diagnostics_summary()

    def _fill_profile_status(self) -> None:
        paths = get_runtime_paths()
        self.profile_status_label.setText(f"Профиль: {paths.profile_root.name}")
        self.profile_status_label.setToolTip(str(paths.profile_root))
        self.database_status_label.setText(
            "База: доступна" if paths.db_path.exists() else "База: будет создана"
        )
        last_self_check = get_last_self_check()
        if not last_self_check:
            self.dashboard_diagnostics_label.setText("Диагностика: самопроверка не запускалась")
            return
        issues = last_self_check.get("issues", [])
        created_at = last_self_check.get("created_at", "-")
        self.dashboard_diagnostics_label.setText(
            f"Диагностика: проблем - {len(issues)}, проверка - {created_at}"
        )

    def _fill_summary(self) -> None:
        counts = {
            "players": self._count_rows("players"),
            "tournaments": self._count_rows("tournaments"),
            "drafts": self._count_rows("tournaments", "status = ?", ("draft",)),
            "review": self._count_rows("tournaments", "status = ?", ("review",)),
            "published": self._count_rows("tournaments", "status = ?", ("published",)),
            "follow_up": self._count_rows("notes", "note_type = ? AND is_archived = 0", ("follow_up",)),
            "restore_points": self._count_rows("restore_points"),
        }
        titles = {
            "players": "Игроки",
            "tournaments": "Турниры",
            "drafts": "Черновики",
            "review": "На проверке",
            "published": "Опубликованы",
            "follow_up": "Контрольные заметки",
            "restore_points": "Точки восстановления",
        }
        for key, value in counts.items():
            self.summary_labels[key].setText(f"{titles[key]}: {value}")

    def _fill_attention(self) -> None:
        self.attention_table.setRowCount(0)
        for tournament in self._tournament_repo.list():
            status = str(tournament.get("status") or "")
            if status not in {"draft", "review"}:
                continue
            action = "Проверить и отправить на публикацию" if status == "draft" else "Подтвердить или вернуть к правкам"
            self._append_attention_row(
                "Турнир",
                str(tournament.get("name") or "Без названия"),
                action,
            )
            if self.attention_table.rowCount() >= 4:
                break

        for report_record in list_import_reports(self._connection):
            report = report_record.report
            if report.warnings_count <= 0 and report.errors_count <= 0:
                continue
            details = "; ".join(report.warnings[:2]) or "Проверить отчет импорта"
            self._append_attention_row("Импорт", report.tournament_name, details)
            if self.attention_table.rowCount() >= 6:
                break

        last_self_check = get_last_self_check()
        issues = last_self_check.get("issues", []) if last_self_check else []
        if issues:
            self._append_attention_row("Диагностика", "Самопроверка", "; ".join(str(issue) for issue in issues[:2]))

    def _append_attention_row(self, priority: str, scenario: str, action: str) -> None:
        row_index = self.attention_table.rowCount()
        self.attention_table.insertRow(row_index)
        for column, value in enumerate([priority, scenario, action]):
            self.attention_table.setItem(row_index, column, QTableWidgetItem(value))

    def _count_rows(
        self,
        table_name: str,
        where_sql: str | None = None,
        params: tuple[object, ...] = (),
    ) -> int:
        query = f"SELECT COUNT(*) AS count FROM {table_name}"
        if where_sql:
            query += f" WHERE {where_sql}"
        row = self._connection.execute(query, params).fetchone()
        return int(row["count"] if row is not None else 0)

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

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.db.database import get_connection
from app.db.repositories import TournamentRepository
from app.runtime_paths import get_runtime_paths
from app.services.import_report import list_import_reports
from app.settings import get_appearance_settings, get_last_self_check
from app.ui.labels import tournament_status_label
from app.ui.player_card_dialog import PlayerCardDialog
from app.ui.welcome_widget import WelcomeWidget


class DashboardView(QWidget):
    def __init__(self, *, navigate: Callable[[str], None] | None = None) -> None:
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._connection = get_connection()
        self._navigate = navigate
        self._tournament_repo = TournamentRepository(self._connection)

        root_layout = QVBoxLayout(self)

        self._stacked = QStackedWidget(self)
        root_layout.addWidget(self._stacked)

        # Page 0: welcome widget
        self._welcome_widget = WelcomeWidget(self)
        self._stacked.addWidget(self._welcome_widget)

        # Page 1: main content with card grid
        self._main_content = QWidget(self)
        layout = QVBoxLayout(self._main_content)

        self.branding_label = self._build_branding_label()
        layout.addWidget(self.branding_label)

        layout.addWidget(QLabel("\u0413\u043b\u0430\u0432\u043d\u0430\u044f", self._main_content))

        # Card grid layout
        cards_grid = QGridLayout()

        # Row 0: Profile status and Quick actions
        cards_grid.addWidget(self._build_profile_status_group(), 0, 0)
        quick_actions_group = QGroupBox("\u0411\u044b\u0441\u0442\u0440\u044b\u0435 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u044f", self._main_content)
        qa_layout = QVBoxLayout(quick_actions_group)
        qa_buttons_layout = self._build_quick_actions()
        qa_layout.addLayout(qa_buttons_layout)
        cards_grid.addWidget(quick_actions_group, 0, 1)

        # Row 1: Summary and Attention
        cards_grid.addWidget(self._build_summary_group(), 1, 0)
        cards_grid.addWidget(self._build_attention_group(), 1, 1)

        # Row 2: Recent tournaments (full width)
        tournaments_group = QGroupBox("\u041f\u043e\u0441\u043b\u0435\u0434\u043d\u0438\u0435 \u0442\u0443\u0440\u043d\u0438\u0440\u044b", self._main_content)
        t_layout = QVBoxLayout(tournaments_group)
        self.recent_tournaments_table = QTableWidget(0, 3, tournaments_group)
        self.recent_tournaments_table.setHorizontalHeaderLabels(["\u0414\u0430\u0442\u0430", "\u0422\u0443\u0440\u043d\u0438\u0440", "\u0421\u0442\u0430\u0442\u0443\u0441"])
        self._configure_table(self.recent_tournaments_table)
        header = self.recent_tournaments_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        t_layout.addWidget(self.recent_tournaments_table)
        cards_grid.addWidget(tournaments_group, 2, 0, 1, 2)

        layout.addLayout(cards_grid)

        self.diagnostics_summary_label = QLabel("\u0414\u0438\u0430\u0433\u043d\u043e\u0441\u0442\u0438\u043a\u0430: \u0441\u0430\u043c\u043e\u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u0435\u0449\u0435 \u043d\u0435 \u0437\u0430\u043f\u0443\u0441\u043a\u0430\u043b\u0430\u0441\u044c", self._main_content)
        layout.addWidget(self.diagnostics_summary_label)

        layout.addStretch(1)

        self._stacked.addWidget(self._main_content)
        self.refresh()

    @staticmethod
    def _configure_table(table: QTableWidget) -> None:
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        table.setWordWrap(True)

    def _build_branding_label(self) -> QLabel:
        appearance = get_appearance_settings()
        logo_path = appearance.get("custom_logo_path")
        label = QLabel(self)
        if logo_path and isinstance(logo_path, str) and Path(logo_path).is_file():
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                label.setPixmap(
                    pixmap.scaledToHeight(60, Qt.TransformationMode.SmoothTransformation)
                )
                return label
        label.setText("<b>\u0414\u0430\u0440\u0442\u0441 \u041b\u0438\u0433\u0430</b>")
        return label

    def _build_quick_actions(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        actions = [
            ("\u0420\u0435\u0439\u0442\u0438\u043d\u0433", "\u0420\u0435\u0439\u0442\u0438\u043d\u0433", "\u041e\u0442\u043a\u0440\u044b\u0442\u044c \u0442\u0435\u043a\u0443\u0449\u0438\u0435 \u0440\u0435\u0439\u0442\u0438\u043d\u0433\u0438 \u043f\u043e \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f\u043c \u0438 \u0432\u0437\u0440\u043e\u0441\u043b\u044b\u043c \u0437\u0430\u0447\u0435\u0442\u0430\u043c."),
            ("\u0422\u0443\u0440\u043d\u0438\u0440\u044b", "\u0422\u0443\u0440\u043d\u0438\u0440\u044b", "\u041e\u0442\u043a\u0440\u044b\u0442\u044c \u0442\u0443\u0440\u043d\u0438\u0440\u044b, \u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u044e \u0438 \u043a\u043e\u0440\u0440\u0435\u043a\u0442\u0438\u0440\u043e\u0432\u043a\u0438."),
            ("\u0418\u0433\u0440\u043e\u043a\u0438", "\u0418\u0433\u0440\u043e\u043a\u0438", "\u041e\u0442\u043a\u0440\u044b\u0442\u044c \u0441\u043f\u0438\u0441\u043e\u043a \u0438\u0433\u0440\u043e\u043a\u043e\u0432 \u0438 \u043a\u0430\u0440\u0442\u043e\u0447\u043a\u0438."),
            ("\u0418\u043c\u043f\u043e\u0440\u0442", "\u0418\u043c\u043f\u043e\u0440\u0442/\u042d\u043a\u0441\u043f\u043e\u0440\u0442", "\u0418\u043c\u043f\u043e\u0440\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c XLSX \u0438 \u043f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u043e\u0442\u0447\u0435\u0442 \u043f\u0435\u0440\u0435\u0434 \u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0435\u0439."),
            ("\u041e\u0442\u0447\u0435\u0442\u044b", "\u041e\u0442\u0447\u0435\u0442\u044b", "\u041e\u0442\u043a\u0440\u044b\u0442\u044c \u044d\u043a\u0441\u043f\u043e\u0440\u0442, \u0436\u0443\u0440\u043d\u0430\u043b \u0438 \u0438\u0441\u0442\u043e\u0440\u0438\u044e \u0438\u043c\u043f\u043e\u0440\u0442\u043e\u0432."),
            ("\u0414\u0438\u0430\u0433\u043d\u043e\u0441\u0442\u0438\u043a\u0430", "\u0414\u0438\u0430\u0433\u043d\u043e\u0441\u0442\u0438\u043a\u0430", "\u041f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u043f\u0440\u043e\u0444\u0438\u043b\u044c, \u043b\u043e\u0433\u0438 \u0438 \u0442\u043e\u0447\u043a\u0438 \u0432\u043e\u0441\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u044f."),
        ]
        for label, target, tooltip in actions:
            button = QPushButton(label, self)
            button.setToolTip(tooltip)
            button.clicked.connect(lambda _checked=False, target=target: self._navigate_to(target))
            layout.addWidget(button)
        layout.addStretch(1)
        return layout

    def _build_profile_status_group(self) -> QGroupBox:
        group = QGroupBox("\u0421\u0442\u0430\u0442\u0443\u0441 \u0440\u0430\u0431\u043e\u0447\u0435\u0433\u043e \u043f\u0440\u043e\u0444\u0438\u043b\u044f", self)
        layout = QGridLayout(group)
        self.profile_status_label = QLabel("\u041f\u0440\u043e\u0444\u0438\u043b\u044c: -", group)
        self.database_status_label = QLabel("\u0411\u0430\u0437\u0430: -", group)
        self.dashboard_diagnostics_label = QLabel("\u0414\u0438\u0430\u0433\u043d\u043e\u0441\u0442\u0438\u043a\u0430: -", group)
        self.refresh_button = QPushButton("\u041e\u0431\u043d\u043e\u0432\u0438\u0442\u044c", group)
        self.refresh_button.setToolTip("\u041e\u0431\u043d\u043e\u0432\u0438\u0442\u044c \u0441\u0432\u043e\u0434\u043a\u0443 \u0433\u043b\u0430\u0432\u043d\u043e\u0439 \u0441\u0442\u0440\u0430\u043d\u0438\u0446\u044b.")
        self.refresh_button.clicked.connect(self.refresh)
        layout.addWidget(self.profile_status_label, 0, 0)
        layout.addWidget(self.database_status_label, 0, 1)
        layout.addWidget(self.dashboard_diagnostics_label, 0, 2)
        layout.addWidget(self.refresh_button, 0, 3)
        return group

    def _build_summary_group(self) -> QGroupBox:
        group = QGroupBox("\u041e\u043f\u0435\u0440\u0430\u0446\u0438\u043e\u043d\u043d\u0430\u044f \u0441\u0432\u043e\u0434\u043a\u0430", self)
        layout = QGridLayout(group)
        self.summary_labels: dict[str, QLabel] = {}
        entries = [
            ("players", "\u0418\u0433\u0440\u043e\u043a\u0438"),
            ("tournaments", "\u0422\u0443\u0440\u043d\u0438\u0440\u044b"),
            ("drafts", "\u0427\u0435\u0440\u043d\u043e\u0432\u0438\u043a\u0438"),
            ("review", "\u041d\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0435"),
            ("published", "\u041e\u043f\u0443\u0431\u043b\u0438\u043a\u043e\u0432\u0430\u043d\u044b"),
            ("follow_up", "\u041a\u043e\u043d\u0442\u0440\u043e\u043b\u044c\u043d\u044b\u0435 \u0437\u0430\u043c\u0435\u0442\u043a\u0438"),
            ("restore_points", "\u0422\u043e\u0447\u043a\u0438 \u0432\u043e\u0441\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u044f"),
        ]
        for index, (key, title) in enumerate(entries):
            label = QLabel(f"{title}: 0", group)
            self.summary_labels[key] = label
            layout.addWidget(label, index // 4, index % 4)
        return group

    def _build_attention_group(self) -> QGroupBox:
        group = QGroupBox("\u0422\u0440\u0435\u0431\u0443\u0435\u0442 \u0432\u043d\u0438\u043c\u0430\u043d\u0438\u044f", self)
        layout = QVBoxLayout(group)
        self.attention_table = QTableWidget(0, 3, group)
        self.attention_table.setHorizontalHeaderLabels(["\u041f\u0440\u0438\u043e\u0440\u0438\u0442\u0435\u0442", "\u0421\u0446\u0435\u043d\u0430\u0440\u0438\u0439", "\u0427\u0442\u043e \u0441\u0434\u0435\u043b\u0430\u0442\u044c"])
        self._configure_table(self.attention_table)
        header = self.attention_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.attention_table)
        return group

    def refresh(self) -> None:
        players_count = self._count_rows("players")
        tournaments_count = self._count_rows("tournaments")
        if players_count == 0 and tournaments_count == 0:
            self._stacked.setCurrentIndex(0)
        else:
            self._stacked.setCurrentIndex(1)
        self._fill_profile_status()
        self._fill_summary()
        self._fill_attention()
        self._fill_recent_tournaments()
        self._fill_diagnostics_summary()

    def _fill_profile_status(self) -> None:
        paths = get_runtime_paths()
        self.profile_status_label.setText(f"\u041f\u0440\u043e\u0444\u0438\u043b\u044c: {paths.profile_root.name}")
        self.profile_status_label.setToolTip(str(paths.profile_root))
        self.database_status_label.setText(
            "\u0411\u0430\u0437\u0430: \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u0430" if paths.db_path.exists() else "\u0411\u0430\u0437\u0430: \u0431\u0443\u0434\u0435\u0442 \u0441\u043e\u0437\u0434\u0430\u043d\u0430"
        )
        last_self_check = get_last_self_check()
        if not last_self_check:
            self.dashboard_diagnostics_label.setText("\u0414\u0438\u0430\u0433\u043d\u043e\u0441\u0442\u0438\u043a\u0430: \u0441\u0430\u043c\u043e\u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u043d\u0435 \u0437\u0430\u043f\u0443\u0441\u043a\u0430\u043b\u0430\u0441\u044c")
            return
        issues = last_self_check.get("issues", [])
        created_at = last_self_check.get("created_at", "-")
        self.dashboard_diagnostics_label.setText(
            f"\u0414\u0438\u0430\u0433\u043d\u043e\u0441\u0442\u0438\u043a\u0430: \u043f\u0440\u043e\u0431\u043b\u0435\u043c - {len(issues)}, \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 - {created_at}"
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
            "players": "\u0418\u0433\u0440\u043e\u043a\u0438",
            "tournaments": "\u0422\u0443\u0440\u043d\u0438\u0440\u044b",
            "drafts": "\u0427\u0435\u0440\u043d\u043e\u0432\u0438\u043a\u0438",
            "review": "\u041d\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0435",
            "published": "\u041e\u043f\u0443\u0431\u043b\u0438\u043a\u043e\u0432\u0430\u043d\u044b",
            "follow_up": "\u041a\u043e\u043d\u0442\u0440\u043e\u043b\u044c\u043d\u044b\u0435 \u0437\u0430\u043c\u0435\u0442\u043a\u0438",
            "restore_points": "\u0422\u043e\u0447\u043a\u0438 \u0432\u043e\u0441\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u044f",
        }
        for key, value in counts.items():
            self.summary_labels[key].setText(f"{titles[key]}: {value}")

    def _fill_attention(self) -> None:
        self.attention_table.setRowCount(0)
        for tournament in self._tournament_repo.list():
            status = str(tournament.get("status") or "")
            if status not in {"draft", "review"}:
                continue
            action = "\u041f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u0438 \u043e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043d\u0430 \u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u044e" if status == "draft" else "\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u044c \u0438\u043b\u0438 \u0432\u0435\u0440\u043d\u0443\u0442\u044c \u043a \u043f\u0440\u0430\u0432\u043a\u0430\u043c"
            self._append_attention_row(
                "\u0422\u0443\u0440\u043d\u0438\u0440",
                str(tournament.get("name") or "\u0411\u0435\u0437 \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u044f"),
                action,
            )
            if self.attention_table.rowCount() >= 4:
                break

        for report_record in list_import_reports(self._connection):
            report = report_record.report
            if report.warnings_count <= 0 and report.errors_count <= 0:
                continue
            details = "; ".join(report.warnings[:2]) or "\u041f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u043e\u0442\u0447\u0435\u0442 \u0438\u043c\u043f\u043e\u0440\u0442\u0430"
            self._append_attention_row("\u0418\u043c\u043f\u043e\u0440\u0442", report.tournament_name, details)
            if self.attention_table.rowCount() >= 6:
                break

        last_self_check = get_last_self_check()
        issues = last_self_check.get("issues", []) if last_self_check else []
        if issues:
            self._append_attention_row("\u0414\u0438\u0430\u0433\u043d\u043e\u0441\u0442\u0438\u043a\u0430", "\u0421\u0430\u043c\u043e\u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430", "; ".join(str(issue) for issue in issues[:2]))

    def _append_attention_row(self, priority: str, scenario: str, action: str) -> None:
        row_index = self.attention_table.rowCount()
        self.attention_table.insertRow(row_index)
        for column, value in enumerate([priority, scenario, action]):
            item = QTableWidgetItem(value)
            item.setToolTip(value)
            self.attention_table.setItem(row_index, column, item)

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
                item = QTableWidgetItem("" if value is None else str(value))
                item.setToolTip("" if value is None else str(value))
                self.recent_tournaments_table.setItem(row_index, column, item)

    def _fill_diagnostics_summary(self) -> None:
        last_self_check = get_last_self_check()
        if not last_self_check:
            self.diagnostics_summary_label.setText("\u0414\u0438\u0430\u0433\u043d\u043e\u0441\u0442\u0438\u043a\u0430: \u0441\u0430\u043c\u043e\u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u0435\u0449\u0435 \u043d\u0435 \u0437\u0430\u043f\u0443\u0441\u043a\u0430\u043b\u0430\u0441\u044c")
            return
        issues = last_self_check.get("issues", [])
        created_at = last_self_check.get("created_at", "-")
        self.diagnostics_summary_label.setText(
            f"\u0414\u0438\u0430\u0433\u043d\u043e\u0441\u0442\u0438\u043a\u0430: \u043f\u0440\u043e\u0431\u043b\u0435\u043c - {len(issues)}, \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u044f\u044f \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 - {created_at}"
        )

    def _navigate_to(self, target: str) -> None:
        if self._navigate is not None:
            self._navigate(target)

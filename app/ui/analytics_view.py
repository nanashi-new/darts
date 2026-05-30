"""Analytics view with sub-tabs for tournaments, players, and comparisons."""

from __future__ import annotations

import logging

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.db.database import get_connection
from app.services.analytics import AnalyticsService

logger = logging.getLogger(__name__)


class TournamentAnalyticsTab(QWidget):
    """Sub-tab for tournament analytics."""

    def __init__(self) -> None:
        super().__init__()
        self._service = AnalyticsService()
        layout = QVBoxLayout(self)

        # Tournament selection
        selection_layout = QHBoxLayout()
        selection_layout.addWidget(QLabel("Турнир:"))
        self._tournament_combo = QComboBox()
        self._tournament_combo.setObjectName("tournament_analytics_combo")
        selection_layout.addWidget(self._tournament_combo)
        load_btn = QPushButton("Загрузить")
        load_btn.setToolTip("Загрузить статистику выбранного турнира")
        load_btn.clicked.connect(self._load_stats)
        selection_layout.addWidget(load_btn)
        layout.addLayout(selection_layout)

        # Stats table
        layout.addWidget(QLabel("Статистика турнира:"))
        self._stats_table = QTableWidget()
        self._stats_table.setObjectName("tournament_stats_table")
        self._stats_table.setColumnCount(2)
        self._stats_table.setHorizontalHeaderLabels(["Показатель", "Значение"])
        layout.addWidget(self._stats_table)

        # Trends section
        layout.addWidget(QLabel("Тенденции (по месяцам):"))
        self._trends_table = QTableWidget()
        self._trends_table.setObjectName("tournament_trends_table")
        self._trends_table.setColumnCount(4)
        self._trends_table.setHorizontalHeaderLabels([
            "Период", "Кол-во турниров", "Среднее участников", "Средний уровень"
        ])
        layout.addWidget(self._trends_table)

        self._load_tournaments()

    def _load_tournaments(self) -> None:
        try:
            connection = get_connection()
            rows = connection.execute(
                "SELECT id, name, date FROM tournaments ORDER BY date DESC, name"
            ).fetchall()
            self._tournament_combo.clear()
            for row in rows:
                self._tournament_combo.addItem(
                    f"{row[1]} ({row[2]})", userData=int(row[0])
                )
        except Exception:  # noqa: BLE001
            logger.exception("Failed to load tournaments list")

    def _load_stats(self) -> None:
        tournament_id = self._tournament_combo.currentData()
        if tournament_id is None:
            return
        try:
            connection = get_connection()
            stats = self._service.tournament_stats(connection, int(tournament_id))
            self._stats_table.setRowCount(0)
            if stats is None:
                return
            data = [
                ("Среднее очков", f"{stats.avg_points:.1f}"),
                ("Медиана очков", f"{stats.median_points:.1f}"),
                ("Минимум очков", str(stats.min_points)),
                ("Максимум очков", str(stats.max_points)),
                ("Участников", str(stats.participant_count)),
            ]
            for place, count in sorted(stats.place_distribution.items()):
                data.append((f"Место {place}", str(count)))
            self._stats_table.setRowCount(len(data))
            for i, (label, value) in enumerate(data):
                self._stats_table.setItem(i, 0, QTableWidgetItem(label))
                self._stats_table.setItem(i, 1, QTableWidgetItem(value))

            # Load trends
            trends = self._service.tournament_trends(connection)
            self._trends_table.setRowCount(len(trends))
            for i, entry in enumerate(trends):
                self._trends_table.setItem(i, 0, QTableWidgetItem(entry.period))
                self._trends_table.setItem(
                    i, 1, QTableWidgetItem(str(entry.tournament_count))
                )
                self._trends_table.setItem(
                    i, 2, QTableWidgetItem(f"{entry.avg_participants:.1f}")
                )
                self._trends_table.setItem(
                    i, 3, QTableWidgetItem(f"{entry.avg_level:.1f}")
                )
        except Exception:  # noqa: BLE001
            logger.exception("Failed to load tournament stats")


class PlayerAnalyticsTab(QWidget):
    """Sub-tab for player analytics."""

    def __init__(self) -> None:
        super().__init__()
        self._service = AnalyticsService()
        layout = QVBoxLayout(self)

        # Player selection
        selection_layout = QHBoxLayout()
        selection_layout.addWidget(QLabel("Игрок:"))
        self._player_combo = QComboBox()
        self._player_combo.setObjectName("player_analytics_combo")
        selection_layout.addWidget(self._player_combo)
        load_btn = QPushButton("Загрузить")
        load_btn.setToolTip("Загрузить прогресс выбранного игрока")
        load_btn.clicked.connect(self._load_progress)
        selection_layout.addWidget(load_btn)
        layout.addLayout(selection_layout)

        # Progress table
        layout.addWidget(QLabel("Прогресс по турнирам:"))
        self._progress_table = QTableWidget()
        self._progress_table.setObjectName("player_progress_table")
        self._progress_table.setColumnCount(4)
        self._progress_table.setHorizontalHeaderLabels([
            "Турнир", "Дата", "Место", "Очки"
        ])
        layout.addWidget(self._progress_table)

        # Summary stats
        self._summary_label = QLabel("")
        self._summary_label.setObjectName("player_summary_label")
        self._summary_label.setWordWrap(True)
        layout.addWidget(self._summary_label)

        self._load_players()

    def _load_players(self) -> None:
        try:
            connection = get_connection()
            rows = connection.execute(
                "SELECT id, last_name, first_name FROM players ORDER BY last_name, first_name"
            ).fetchall()
            self._player_combo.clear()
            for row in rows:
                self._player_combo.addItem(
                    f"{row[1]} {row[2]}", userData=int(row[0])
                )
        except Exception:  # noqa: BLE001
            logger.exception("Failed to load players list")

    def _load_progress(self) -> None:
        player_id = self._player_combo.currentData()
        if player_id is None:
            return
        try:
            connection = get_connection()
            progress = self._service.player_progress(connection, int(player_id))
            self._progress_table.setRowCount(len(progress))
            for i, entry in enumerate(progress):
                self._progress_table.setItem(
                    i, 0, QTableWidgetItem(entry.tournament_name)
                )
                self._progress_table.setItem(i, 1, QTableWidgetItem(entry.date))
                self._progress_table.setItem(
                    i, 2, QTableWidgetItem(str(entry.place))
                )
                self._progress_table.setItem(
                    i, 3, QTableWidgetItem(str(entry.points_total))
                )

            # Summary
            comparison = self._service.compare_players(connection, [int(player_id)])
            stability = self._service.player_stability(connection, int(player_id))
            if comparison:
                c = comparison[0]
                win_pct = (
                    (c.win_count / c.tournaments_count * 100)
                    if c.tournaments_count > 0
                    else 0.0
                )
                self._summary_label.setText(
                    f"Турниров: {c.tournaments_count} | "
                    f"Среднее очков: {c.avg_points:.1f} | "
                    f"Средняя позиция: {c.avg_position:.1f} | "
                    f"Лучшая: {c.best_position} | "
                    f"Худшая: {c.worst_position} | "
                    f"Побед: {c.win_count} ({win_pct:.0f}%) | "
                    f"Стабильность (СО): {stability:.1f}"
                )
            else:
                self._summary_label.setText("")
        except Exception:  # noqa: BLE001
            logger.exception("Failed to load player progress")


class ComparisonTab(QWidget):
    """Sub-tab for comparing tournaments or players."""

    def __init__(self) -> None:
        super().__init__()
        self._service = AnalyticsService()
        layout = QVBoxLayout(self)

        # Mode selection
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Режим:"))
        self._mode_combo = QComboBox()
        self._mode_combo.setObjectName("comparison_mode_combo")
        self._mode_combo.addItems(["Турниры", "Игроки"])
        self._mode_combo.currentIndexChanged.connect(self._refresh_list)
        mode_layout.addWidget(self._mode_combo)
        layout.addLayout(mode_layout)

        # Selection list (multi-select)
        layout.addWidget(QLabel("Выберите элементы (множественный выбор):"))
        self._selection_list = QListWidget()
        self._selection_list.setObjectName("comparison_selection_list")
        self._selection_list.setSelectionMode(
            QListWidget.SelectionMode.MultiSelection
        )
        layout.addWidget(self._selection_list)

        compare_btn = QPushButton("Сравнить")
        compare_btn.setToolTip("Сравнить выбранные элементы")
        compare_btn.clicked.connect(self._compare)
        layout.addWidget(compare_btn)

        # Results table
        self._results_table = QTableWidget()
        self._results_table.setObjectName("comparison_results_table")
        layout.addWidget(self._results_table)

        self._refresh_list()

    def _refresh_list(self) -> None:
        self._selection_list.clear()
        try:
            connection = get_connection()
            if self._mode_combo.currentText() == "Турниры":
                rows = connection.execute(
                    "SELECT id, name, date FROM tournaments ORDER BY date DESC, name"
                ).fetchall()
                for row in rows:
                    item_text = f"{row[1]} ({row[2]})"
                    self._selection_list.addItem(item_text)
                    item = self._selection_list.item(self._selection_list.count() - 1)
                    if item is not None:
                        item.setData(256, int(row[0]))  # Qt.ItemDataRole.UserRole = 256
            else:
                rows = connection.execute(
                    "SELECT id, last_name, first_name FROM players ORDER BY last_name, first_name"
                ).fetchall()
                for row in rows:
                    item_text = f"{row[1]} {row[2]}"
                    self._selection_list.addItem(item_text)
                    item = self._selection_list.item(self._selection_list.count() - 1)
                    if item is not None:
                        item.setData(256, int(row[0]))
        except Exception:  # noqa: BLE001
            logger.exception("Failed to refresh comparison list")

    def _compare(self) -> None:
        selected_items = self._selection_list.selectedItems()
        if not selected_items:
            return
        ids = [item.data(256) for item in selected_items if item.data(256) is not None]
        if not ids:
            return
        try:
            connection = get_connection()
            if self._mode_combo.currentText() == "Турниры":
                entries = self._service.compare_tournaments(connection, ids)
                self._results_table.setColumnCount(5)
                self._results_table.setHorizontalHeaderLabels([
                    "Турнир", "Дата", "Среднее очков", "Участников", "Лучший результат"
                ])
                self._results_table.setRowCount(len(entries))
                for i, e in enumerate(entries):
                    self._results_table.setItem(i, 0, QTableWidgetItem(e.name))
                    self._results_table.setItem(i, 1, QTableWidgetItem(e.date))
                    self._results_table.setItem(
                        i, 2, QTableWidgetItem(f"{e.avg_points:.1f}")
                    )
                    self._results_table.setItem(
                        i, 3, QTableWidgetItem(str(e.participant_count))
                    )
                    self._results_table.setItem(
                        i, 4, QTableWidgetItem(str(e.top_score))
                    )
            else:
                entries_p = self._service.compare_players(connection, ids)
                self._results_table.setColumnCount(8)
                self._results_table.setHorizontalHeaderLabels([
                    "Игрок", "Турниров", "Среднее очков", "Средняя позиция",
                    "Лучшая", "Худшая", "Побед", "Стабильность"
                ])
                self._results_table.setRowCount(len(entries_p))
                for i, e in enumerate(entries_p):
                    self._results_table.setItem(i, 0, QTableWidgetItem(e.fio))
                    self._results_table.setItem(
                        i, 1, QTableWidgetItem(str(e.tournaments_count))
                    )
                    self._results_table.setItem(
                        i, 2, QTableWidgetItem(f"{e.avg_points:.1f}")
                    )
                    self._results_table.setItem(
                        i, 3, QTableWidgetItem(f"{e.avg_position:.1f}")
                    )
                    self._results_table.setItem(
                        i, 4, QTableWidgetItem(str(e.best_position))
                    )
                    self._results_table.setItem(
                        i, 5, QTableWidgetItem(str(e.worst_position))
                    )
                    self._results_table.setItem(
                        i, 6, QTableWidgetItem(str(e.win_count))
                    )
                    self._results_table.setItem(
                        i, 7, QTableWidgetItem(f"{e.stability:.1f}")
                    )
        except Exception:  # noqa: BLE001
            logger.exception("Failed to compare items")


class AnalyticsView(QWidget):
    """Main analytics view with sub-tabs."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        tabs.setObjectName("analytics_tabs")
        tabs.addTab(TournamentAnalyticsTab(), "Турниры")
        tabs.addTab(PlayerAnalyticsTab(), "Игроки")
        tabs.addTab(ComparisonTab(), "Сравнение")
        layout.addWidget(tabs)

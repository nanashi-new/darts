from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QSizePolicy, QStatusBar, QTabWidget

from app.db.database import get_connection
from app.runtime_paths import get_runtime_paths
from app.ui.about_view import AboutView
from app.ui.analytics_view import AnalyticsView
from app.ui.coach_view import CoachView
from app.ui.context_view import ContextView
from app.ui.dashboard_view import DashboardView
from app.ui.diagnostics_view import DiagnosticsView
from app.ui.faq_view import FaqView
from app.ui.import_export_view import ImportExportView
from app.ui.players_view import PlayersView
from app.ui.rating_view import RatingView
from app.ui.reports_view import ReportsView
from app.ui.settings_view import SettingsView
from app.ui.tournaments_view import TournamentsView
from app.ui_state import get_view_state, update_view_state


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Дартс Лига")
        self.setMinimumSize(1280, 720)

        tabs = QTabWidget()
        tabs.setObjectName("main_workspace_tabs")
        tabs.setUsesScrollButtons(True)
        tabs.setDocumentMode(True)
        tabs.setElideMode(Qt.TextElideMode.ElideRight)
        tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        tabs.addTab(DashboardView(navigate=lambda target: self._activate_tab(tabs, target)), "Главная")
        tabs.addTab(RatingView(), "Рейтинг")
        tournaments_view = TournamentsView()
        tabs.addTab(tournaments_view, "Турниры")
        tabs.addTab(PlayersView(), "Игроки")
        tabs.addTab(ContextView(), "Контекст")
        tabs.addTab(CoachView(), "Тренер")
        tabs.addTab(AnalyticsView(), "Аналитика")
        tabs.addTab(ImportExportView(tournaments_view), "Импорт/Экспорт")
        tabs.addTab(ReportsView(), "Отчеты")
        tabs.addTab(DiagnosticsView(), "Диагностика")
        tabs.addTab(FaqView(), "Вопросы и ответы")
        tabs.addTab(SettingsView(), "Настройки")
        tabs.addTab(AboutView(), "О программе")

        self._tabs = tabs
        self.setCentralWidget(tabs)
        self._setup_status_bar()
        self._restore_state()
        tabs.currentChanged.connect(self._persist_state)
        tabs.currentChanged.connect(lambda _idx: self._refresh_status_bar())

    def _setup_status_bar(self) -> None:
        status_bar = QStatusBar(self)
        self.setStatusBar(status_bar)
        self._players_count_label = QLabel("Игроки: 0")
        self._tournaments_count_label = QLabel("Турниры: 0")
        self._profile_name_label = QLabel("Профиль: -")
        status_bar.addPermanentWidget(self._players_count_label)
        status_bar.addPermanentWidget(self._tournaments_count_label)
        status_bar.addPermanentWidget(self._profile_name_label)
        self._refresh_status_bar()

    def _refresh_status_bar(self) -> None:
        try:
            connection = get_connection()
            players_count = connection.execute("SELECT COUNT(*) AS cnt FROM players").fetchone()
            tournaments_count = connection.execute("SELECT COUNT(*) AS cnt FROM tournaments").fetchone()
            p_count = int(players_count["cnt"]) if players_count else 0
            t_count = int(tournaments_count["cnt"]) if tournaments_count else 0
        except Exception:  # noqa: BLE001
            p_count = 0
            t_count = 0
        self._players_count_label.setText(f"Игроки: {p_count}")
        self._tournaments_count_label.setText(f"Турниры: {t_count}")
        paths = get_runtime_paths()
        self._profile_name_label.setText(f"Профиль: {paths.profile_root.name}")

    def show_workspace(self) -> None:
        self.showMaximized()

    @staticmethod
    def _activate_tab(tabs: QTabWidget, target: str) -> None:
        aliases = {
            "Dashboard": "Главная",
            "Главная": "Главная",
            "Context": "Контекст",
            "Контекст": "Контекст",
            "Coach": "Тренер",
            "Тренер": "Тренер",
            "Analytics": "Аналитика",
            "Аналитика": "Аналитика",
            "Players": "Игроки",
            "Игроки": "Игроки",
            "Tournaments": "Турниры",
            "Турниры": "Турниры",
            "Rating": "Рейтинг",
            "Рейтинг": "Рейтинг",
            "Reports": "Отчеты",
            "Отчеты": "Отчеты",
            "Diagnostics": "Диагностика",
            "Диагностика": "Диагностика",
            "Settings": "Настройки",
            "Настройки": "Настройки",
            "About": "О программе",
            "О программе": "О программе",
        }
        resolved_target = aliases.get(target, target)
        for index in range(tabs.count()):
            if tabs.tabText(index) == resolved_target:
                tabs.setCurrentIndex(index)
                return

    def _restore_state(self) -> None:
        state = get_view_state("main_window")
        target = state.get("current_tab")
        if isinstance(target, str) and target:
            self._activate_tab(self._tabs, target)

    def _persist_state(self, _index: int) -> None:
        update_view_state(
            "main_window",
            {"current_tab": self._tabs.tabText(self._tabs.currentIndex())},
        )

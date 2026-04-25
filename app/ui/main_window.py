from PySide6.QtWidgets import QMainWindow, QTabWidget

from app.ui.about_view import AboutView
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
        self.setMinimumSize(1024, 640)

        tabs = QTabWidget()
        tabs.addTab(DashboardView(navigate=lambda target: self._activate_tab(tabs, target)), "Главная")
        tabs.addTab(RatingView(), "Рейтинг")
        tournaments_view = TournamentsView()
        tabs.addTab(tournaments_view, "Турниры")
        tabs.addTab(PlayersView(), "Игроки")
        tabs.addTab(ContextView(), "Контекст")
        tabs.addTab(ImportExportView(tournaments_view), "Импорт/Экспорт")
        tabs.addTab(ReportsView(), "Отчеты")
        tabs.addTab(DiagnosticsView(), "Диагностика")
        tabs.addTab(FaqView(), "Вопросы и ответы")
        tabs.addTab(SettingsView(), "Настройки")
        tabs.addTab(AboutView(), "О программе")

        self._tabs = tabs
        self.setCentralWidget(tabs)
        self._restore_state()
        tabs.currentChanged.connect(self._persist_state)

    @staticmethod
    def _activate_tab(tabs: QTabWidget, target: str) -> None:
        aliases = {
            "Dashboard": "Главная",
            "Главная": "Главная",
            "Context": "Контекст",
            "Контекст": "Контекст",
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

from PySide6.QtWidgets import QMainWindow, QTabWidget

from app.ui.about_view import AboutView
from app.ui.faq_view import FaqView
from app.ui.import_export_view import ImportExportView
from app.ui.players_view import PlayersView
from app.ui.rating_view import RatingView
from app.ui.reports_view import ReportsView
from app.ui.settings_view import SettingsView
from app.ui.tournaments_view import TournamentsView


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Darts Rating EBCK")
        self.setMinimumSize(1024, 640)

        tabs = QTabWidget()
        tabs.addTab(RatingView(), "Рейтинг")
        tournaments_view = TournamentsView()
        tabs.addTab(tournaments_view, "Турниры")
        tabs.addTab(PlayersView(), "Игроки")
        tabs.addTab(ImportExportView(tournaments_view), "Импорт/Экспорт")
        tabs.addTab(ReportsView(), "Отчёты")
        tabs.addTab(FaqView(), "FAQ")
        tabs.addTab(SettingsView(), "Настройки")
        tabs.addTab(AboutView(), "О программе")

        self.setCentralWidget(tabs)

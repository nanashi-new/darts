from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QStackedWidget,
    QStatusBar,
    QWidget,
)

from app.db.database import get_connection
from app.runtime_paths import get_runtime_paths
from app.ui.about_view import AboutView
from app.ui.analytics_view import AnalyticsView
from app.ui.coach_view import CoachView
from app.ui.context_view import ContextView
from app.ui.dashboard_view import DashboardView
from app.ui.diagnostics_view import DiagnosticsView
from app.ui.faq_view import FaqView
from app.ui.guided_tour import GuidedTour, is_tour_completed
from app.ui.import_export_view import ImportExportView
from app.ui.players_view import PlayersView
from app.ui.rating_view import RatingView
from app.ui.reports_view import ReportsView
from app.ui.settings_view import SettingsView
from app.ui.shortcuts import ShortcutManager
from app.ui.sidebar import SidebarWidget
from app.ui.toast_notification import ToastNotification
from app.ui.tournaments_view import TournamentsView
from app.ui_state import get_view_state, update_view_state


class MainWindow(QMainWindow):
    # Map sidebar item keys to view indices
    _VIEW_KEYS: list[str] = [
        "dashboard",
        "rating",
        "tournaments",
        "players",
        "context",
        "coach",
        "analytics",
        "import_export",
        "reports",
        "diagnostics",
        "faq",
        "settings",
        "about",
    ]

    # Aliases for backward compatibility with _activate_tab
    _ALIASES: dict[str, str] = {
        "Dashboard": "dashboard",
        "\u0413\u043b\u0430\u0432\u043d\u0430\u044f": "dashboard",
        "Context": "context",
        "\u041a\u043e\u043d\u0442\u0435\u043a\u0441\u0442": "context",
        "Coach": "coach",
        "\u0422\u0440\u0435\u043d\u0435\u0440": "coach",
        "Analytics": "analytics",
        "\u0410\u043d\u0430\u043b\u0438\u0442\u0438\u043a\u0430": "analytics",
        "Players": "players",
        "\u0418\u0433\u0440\u043e\u043a\u0438": "players",
        "Tournaments": "tournaments",
        "\u0422\u0443\u0440\u043d\u0438\u0440\u044b": "tournaments",
        "Rating": "rating",
        "\u0420\u0435\u0439\u0442\u0438\u043d\u0433": "rating",
        "Reports": "reports",
        "\u041e\u0442\u0447\u0435\u0442\u044b": "reports",
        "Diagnostics": "diagnostics",
        "\u0414\u0438\u0430\u0433\u043d\u043e\u0441\u0442\u0438\u043a\u0430": "diagnostics",
        "Settings": "settings",
        "\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438": "settings",
        "About": "about",
        "\u041e \u043f\u0440\u043e\u0433\u0440\u0430\u043c\u043c\u0435": "about",
        "\u0421\u043f\u0440\u0430\u0432\u043a\u0430": "faq",
        "FAQ": "faq",
        "Help": "faq",
        "\u0412\u043e\u043f\u0440\u043e\u0441\u044b \u0438 \u043e\u0442\u0432\u0435\u0442\u044b": "faq",
        "\u0418\u043c\u043f\u043e\u0440\u0442/\u042d\u043a\u0441\u043f\u043e\u0440\u0442": "import_export",
        "Import": "import_export",
        "Import/Export": "import_export",
    }

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("\u0414\u0430\u0440\u0442\u0441 \u041b\u0438\u0433\u0430")
        self.setMinimumSize(1280, 720)

        # Container widget with horizontal layout
        container = QWidget()
        container.setObjectName("main_container")
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)

        # Sidebar
        self._sidebar = SidebarWidget(container)
        h_layout.addWidget(self._sidebar)

        # Stacked widget for views
        self._stacked = QStackedWidget(container)
        self._stacked.setObjectName("main_workspace_stack")
        self._stacked.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        tournaments_view = TournamentsView()
        self._views: dict[str, QWidget] = {}
        views_ordered: list[tuple[str, QWidget]] = [
            ("dashboard", DashboardView(navigate=lambda target: self._activate_tab(target))),
            ("rating", RatingView()),
            ("tournaments", tournaments_view),
            ("players", PlayersView()),
            ("context", ContextView()),
            ("coach", CoachView()),
            ("analytics", AnalyticsView()),
            ("import_export", ImportExportView(tournaments_view)),
            ("reports", ReportsView()),
            ("diagnostics", DiagnosticsView()),
            ("faq", FaqView()),
            ("settings", SettingsView()),
            ("about", AboutView()),
        ]
        for key, view in views_ordered:
            self._stacked.addWidget(view)
            self._views[key] = view

        h_layout.addWidget(self._stacked, 1)

        # Keep _tabs as a backward-compatible reference to stacked widget
        self._tabs = self._stacked

        self.setCentralWidget(container)
        self._setup_status_bar()
        self._restore_state()
        self._sidebar.navigation_changed.connect(self._on_sidebar_navigation)
        self._setup_guided_tour()
        self._shortcut_manager = ShortcutManager(self)
        self.setAcceptDrops(True)

    def _on_sidebar_navigation(self, key: str) -> None:
        if key in self._VIEW_KEYS:
            index = self._VIEW_KEYS.index(key)
            self._stacked.setCurrentIndex(index)
            self._persist_state()
            self._refresh_status_bar()

    def _setup_guided_tour(self) -> None:
        """Initialize guided tour overlay, show on first launch."""
        self._guided_tour = GuidedTour(self)
        if not is_tour_completed():
            self._guided_tour.start_tour()

    def _setup_status_bar(self) -> None:
        status_bar = QStatusBar(self)
        self.setStatusBar(status_bar)
        self._players_count_label = QLabel("\u0418\u0433\u0440\u043e\u043a\u0438: 0")
        self._tournaments_count_label = QLabel("\u0422\u0443\u0440\u043d\u0438\u0440\u044b: 0")
        self._profile_name_label = QLabel("\u041f\u0440\u043e\u0444\u0438\u043b\u044c: -")
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
        self._players_count_label.setText(f"\u0418\u0433\u0440\u043e\u043a\u0438: {p_count}")
        self._tournaments_count_label.setText(f"\u0422\u0443\u0440\u043d\u0438\u0440\u044b: {t_count}")
        paths = get_runtime_paths()
        self._profile_name_label.setText(f"\u041f\u0440\u043e\u0444\u0438\u043b\u044c: {paths.profile_root.name}")

    def show_workspace(self) -> None:
        self.showMaximized()

    def _activate_tab(self, target: str) -> None:
        """Navigate to a view by name or alias. Works with both Russian and English names."""
        resolved = self._ALIASES.get(target, target)
        # If resolved is already a valid key, use it
        if resolved in self._VIEW_KEYS:
            index = self._VIEW_KEYS.index(resolved)
            self._stacked.setCurrentIndex(index)
            self._sidebar.set_current_item(resolved)
            self._persist_state()
            return
        # Try the target itself as a key
        if target in self._VIEW_KEYS:
            index = self._VIEW_KEYS.index(target)
            self._stacked.setCurrentIndex(index)
            self._sidebar.set_current_item(target)
            self._persist_state()

    def _restore_state(self) -> None:
        state = get_view_state("main_window")
        target = state.get("current_tab")
        if isinstance(target, str) and target:
            self._activate_tab(target)

    def _persist_state(self) -> None:
        current_key = self._sidebar.current_item()
        update_view_state(
            "main_window",
            {"current_tab": current_key},
        )

    def show_toast(self, message: str, level: str = "info") -> None:
        """Show a non-blocking toast notification."""
        ToastNotification.show_toast(self, message, level)

    def dragEnterEvent(self, event: object) -> None:  # type: ignore[override]
        from PySide6.QtGui import QDragEnterEvent

        if not isinstance(event, QDragEnterEvent):
            return
        mime = event.mimeData()
        if mime is not None and mime.hasUrls():
            event.acceptProposedAction()

    def closeEvent(self, event: object) -> None:  # type: ignore[override]
        from app.services.undo_manager import undo_manager

        undo_manager.clear()
        super().closeEvent(event)  # type: ignore[arg-type]

    def dropEvent(self, event: object) -> None:  # type: ignore[override]
        from PySide6.QtGui import QDropEvent

        if not isinstance(event, QDropEvent):
            return
        mime = event.mimeData()
        if mime is None or not mime.hasUrls():
            return
        paths: list[str] = []
        for url in mime.urls():
            local = url.toLocalFile()
            if local:
                paths.append(local)
        if not paths:
            return
        # Navigate to import view
        self._activate_tab("\u0418\u043c\u043f\u043e\u0440\u0442/\u042d\u043a\u0441\u043f\u043e\u0440\u0442")
        # Trigger import on the import view
        import_view = self._views.get("import_export")
        if isinstance(import_view, ImportExportView):
            import_view.handle_dropped_files(paths)
        event.acceptProposedAction()

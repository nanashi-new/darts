from __future__ import annotations

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.db.database import get_connection
from app.services.audit_log import AuditLogService, RECALC_ALL
from app.services.player_merge import PlayerMergeService
from app.services.recalculate_tournament import recalculate_all_tournaments
from app.settings import get_appearance_settings, update_appearance_settings
from app.ui.player_merge_dialog import PlayerMergeDialog
from app.ui.season_transfer_dialog import SeasonTransferDialog
from app.ui.theme import ThemeManager


_THEME_LABELS = ["Светлая", "Темная"]
_THEME_VALUES = ["light", "dark"]

_ACCENT_LABELS = ["Синий", "Зеленый", "Оранжевый", "Фиолетовый"]
_ACCENT_VALUES = ["#1976D2", "#388E3C", "#F57C00", "#7B1FA2"]

_FONT_SIZE_LABELS = ["Мелкий", "Средний", "Крупный"]
_FONT_SIZE_VALUES = ["small", "medium", "large"]


class SettingsView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._connection = get_connection()
        self._audit_log_service = AuditLogService(self._connection)
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        root_layout.addWidget(scroll_area)

        content = QWidget(self)
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        scroll_area.setWidget(content)

        layout = QVBoxLayout(content)

        # Appearance section
        layout.addWidget(self._build_appearance_group())

        description = QLabel("Служебные действия для обслуживания базы и данных приложения.", self)
        description.setWordWrap(True)
        layout.addWidget(description)

        recalc_all_btn = QPushButton("Пересчитать рейтинг", self)
        recalc_all_btn.clicked.connect(self._recalculate_all)
        layout.addWidget(recalc_all_btn)

        merge_btn = QPushButton("Слияние дублей", self)
        merge_btn.clicked.connect(self._open_player_merge)
        layout.addWidget(merge_btn)

        season_transfer_btn = QPushButton("Сезонные переходы", self)
        season_transfer_btn.setToolTip("Рассчитать и применить сезонные переходы между лигами.")
        season_transfer_btn.clicked.connect(self._open_season_transfer)
        layout.addWidget(season_transfer_btn)

        layout.addStretch(1)

    def _build_appearance_group(self) -> QGroupBox:
        appearance = get_appearance_settings()
        group = QGroupBox("Внешний вид", self)
        layout = QVBoxLayout(group)

        # Theme
        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Тема:", group))
        self._theme_combo = QComboBox(group)
        self._theme_combo.addItems(_THEME_LABELS)
        current_theme = str(appearance.get("theme", "light"))
        if current_theme in _THEME_VALUES:
            self._theme_combo.setCurrentIndex(_THEME_VALUES.index(current_theme))
        theme_row.addWidget(self._theme_combo)
        layout.addLayout(theme_row)

        # Accent color
        accent_row = QHBoxLayout()
        accent_row.addWidget(QLabel("Акцентный цвет:", group))
        self._accent_combo = QComboBox(group)
        self._accent_combo.addItems(_ACCENT_LABELS)
        current_accent = str(appearance.get("accent_color", "#1976D2"))
        if current_accent in _ACCENT_VALUES:
            self._accent_combo.setCurrentIndex(_ACCENT_VALUES.index(current_accent))
        accent_row.addWidget(self._accent_combo)
        layout.addLayout(accent_row)

        # Font size
        font_row = QHBoxLayout()
        font_row.addWidget(QLabel("Размер шрифта:", group))
        self._font_size_combo = QComboBox(group)
        self._font_size_combo.addItems(_FONT_SIZE_LABELS)
        current_font = str(appearance.get("font_size", "medium"))
        if current_font in _FONT_SIZE_VALUES:
            self._font_size_combo.setCurrentIndex(_FONT_SIZE_VALUES.index(current_font))
        font_row.addWidget(self._font_size_combo)
        layout.addLayout(font_row)

        # Custom logo
        logo_row = QHBoxLayout()
        self._logo_button = QPushButton("Логотип...", group)
        self._logo_button.clicked.connect(self._select_logo)
        logo_row.addWidget(self._logo_button)
        logo_path = appearance.get("custom_logo_path")
        self._logo_label = QLabel(
            str(logo_path) if logo_path else "По умолчанию", group
        )
        self._logo_label.setWordWrap(True)
        logo_row.addWidget(self._logo_label, 1)
        layout.addLayout(logo_row)

        # Custom icon
        icon_row = QHBoxLayout()
        self._icon_button = QPushButton("Иконка...", group)
        self._icon_button.clicked.connect(self._select_icon)
        icon_row.addWidget(self._icon_button)
        icon_path = appearance.get("custom_icon_path")
        self._icon_label = QLabel(
            str(icon_path) if icon_path else "По умолчанию", group
        )
        self._icon_label.setWordWrap(True)
        icon_row.addWidget(self._icon_label, 1)
        layout.addLayout(icon_row)

        # Apply button
        self._apply_button = QPushButton("Применить", group)
        self._apply_button.clicked.connect(self._apply_appearance)
        layout.addWidget(self._apply_button)

        return group

    def _select_logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Выбрать логотип", "", "Изображения (*.png *.svg *.jpg)"
        )
        if path:
            self._logo_label.setText(path)

    def _select_icon(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Выбрать иконку", "", "Изображения (*.png *.svg *.jpg)"
        )
        if path:
            self._icon_label.setText(path)

    def _apply_appearance(self) -> None:
        theme = _THEME_VALUES[self._theme_combo.currentIndex()]
        accent = _ACCENT_VALUES[self._accent_combo.currentIndex()]
        font_size = _FONT_SIZE_VALUES[self._font_size_combo.currentIndex()]
        logo_text = self._logo_label.text()
        icon_text = self._icon_label.text()
        logo_path: str | None = None if logo_text == "По умолчанию" else logo_text
        icon_path: str | None = None if icon_text == "По умолчанию" else icon_text

        update_appearance_settings({
            "theme": theme,
            "accent_color": accent,
            "font_size": font_size,
            "custom_logo_path": logo_path,
            "custom_icon_path": icon_path,
        })

        app = QApplication.instance()
        if app is not None:
            ThemeManager.apply_theme(app, theme, accent_color=accent, font_size=font_size)  # type: ignore[arg-type]

    def _recalculate_all(self) -> None:
        report = recalculate_all_tournaments(connection=self._connection)
        self._audit_log_service.log_event(
            RECALC_ALL,
            "Пересчет всех турниров (настройки)",
            (
                f"Турниров: {report.tournaments_processed}; "
                f"обновлено: {report.results_updated}; "
                f"warnings: {len(report.warnings)}; errors: {len(report.errors)}"
            ),
            level="error" if report.errors else "warning" if report.warnings else "info",
        )
        details = [
            f"Турниров: {report.tournaments_processed}",
            f"Обновлено результатов: {report.results_updated}",
            f"Предупреждений: {len(report.warnings)}",
            f"Ошибок: {len(report.errors)}",
        ]
        if report.warnings:
            details.append("\n".join(report.warnings[:3]))
        if report.errors:
            details.append("\n".join(report.errors[:3]))
        QMessageBox.information(self, "Пересчет рейтинга", "\n".join(details))

    def _open_player_merge(self) -> None:
        dialog = PlayerMergeDialog(PlayerMergeService(self._connection), self)
        dialog.exec()

    def _open_season_transfer(self) -> None:
        dialog = SeasonTransferDialog(self)
        dialog.exec()

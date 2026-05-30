from __future__ import annotations

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.db.database import get_connection
from app.runtime_paths import get_profiles_base_dir, get_runtime_paths
from app.services.audit_log import AuditLogService, RECALC_ALL
from app.services.player_merge import PlayerMergeService
from app.services.profile_manager import ProfileManager
from app.services.recalculate_tournament import recalculate_all_tournaments
from app.settings import get_appearance_settings, update_appearance_settings
from app.settings import get_organization_profile, update_organization_profile
from app.ui.player_merge_dialog import PlayerMergeDialog
from app.ui.profile_selector_dialog import ProfileSelectorDialog
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

        # Organization section
        layout.addWidget(self._build_organization_group())

        # Profile section
        layout.addWidget(self._build_profile_group())

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

    def _build_organization_group(self) -> QGroupBox:
        profile = get_organization_profile()
        group = QGroupBox("\u041e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u044f", self)
        layout = QVBoxLayout(group)

        # Org name (multi-line)
        layout.addWidget(QLabel("\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u0438:", group))
        self._org_name_edit = QTextEdit(group)
        self._org_name_edit.setPlaceholderText("\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u0438 (\u0434\u043e 3 \u0441\u0442\u0440\u043e\u043a)")
        self._org_name_edit.setMaximumHeight(70)
        self._org_name_edit.setPlainText(str(profile.get("org_name", "")))
        layout.addWidget(self._org_name_edit)

        # City
        city_row = QHBoxLayout()
        city_row.addWidget(QLabel("\u0413\u043e\u0440\u043e\u0434:", group))
        self._org_city_edit = QLineEdit(group)
        self._org_city_edit.setPlaceholderText("\u0413\u043e\u0440\u043e\u0434")
        self._org_city_edit.setText(str(profile.get("city", "")))
        city_row.addWidget(self._org_city_edit)
        layout.addLayout(city_row)

        # Default venue
        venue_row = QHBoxLayout()
        venue_row.addWidget(QLabel("\u041c\u0435\u0441\u0442\u043e \u043f\u0440\u043e\u0432\u0435\u0434\u0435\u043d\u0438\u044f:", group))
        self._org_venue_edit = QLineEdit(group)
        self._org_venue_edit.setPlaceholderText("\u041c\u0435\u0441\u0442\u043e \u043f\u0440\u043e\u0432\u0435\u0434\u0435\u043d\u0438\u044f \u043f\u043e \u0443\u043c\u043e\u043b\u0447\u0430\u043d\u0438\u044e")
        self._org_venue_edit.setText(str(profile.get("default_venue", "")))
        venue_row.addWidget(self._org_venue_edit)
        layout.addLayout(venue_row)

        # Logo
        logo_row = QHBoxLayout()
        self._org_logo_button = QPushButton("\u041b\u043e\u0433\u043e\u0442\u0438\u043f...", group)
        self._org_logo_button.clicked.connect(self._select_org_logo)
        logo_row.addWidget(self._org_logo_button)
        logo_path = profile.get("logo_path")
        self._org_logo_label = QLabel(
            str(logo_path) if logo_path else "\u041d\u0435 \u0432\u044b\u0431\u0440\u0430\u043d", group
        )
        self._org_logo_label.setWordWrap(True)
        logo_row.addWidget(self._org_logo_label, 1)
        layout.addLayout(logo_row)

        # Jury table
        layout.addWidget(QLabel("\u0421\u0443\u0434\u0435\u0439\u0441\u043a\u0430\u044f \u043a\u043e\u043b\u043b\u0435\u0433\u0438\u044f:", group))
        self._org_jury_table = QTableWidget(group)
        self._org_jury_table.setColumnCount(4)
        self._org_jury_table.setHorizontalHeaderLabels([
            "\u0414\u043e\u043b\u0436\u043d\u043e\u0441\u0442\u044c",
            "\u0424\u0418\u041e",
            "\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f",
            "\u0413\u043e\u0440\u043e\u0434",
        ])
        self._org_jury_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        jury_members = profile.get("jury_members")
        if isinstance(jury_members, list):
            self._org_jury_table.setRowCount(len(jury_members))
            for row_idx, member in enumerate(jury_members):
                if isinstance(member, dict):
                    self._org_jury_table.setItem(row_idx, 0, QTableWidgetItem(str(member.get("position", ""))))
                    self._org_jury_table.setItem(row_idx, 1, QTableWidgetItem(str(member.get("name", ""))))
                    self._org_jury_table.setItem(row_idx, 2, QTableWidgetItem(str(member.get("category", ""))))
                    self._org_jury_table.setItem(row_idx, 3, QTableWidgetItem(str(member.get("city", ""))))
        layout.addWidget(self._org_jury_table)

        # Jury add/remove buttons
        jury_btn_row = QHBoxLayout()
        add_btn = QPushButton("\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c", group)
        add_btn.clicked.connect(self._add_org_jury_row)
        remove_btn = QPushButton("\u0423\u0434\u0430\u043b\u0438\u0442\u044c", group)
        remove_btn.clicked.connect(self._remove_org_jury_row)
        jury_btn_row.addWidget(add_btn)
        jury_btn_row.addWidget(remove_btn)
        jury_btn_row.addStretch(1)
        layout.addLayout(jury_btn_row)

        # Save button
        save_btn = QPushButton("\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c \u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u044e", group)
        save_btn.clicked.connect(self._save_organization_profile)
        layout.addWidget(save_btn)

        return group

    def _select_org_logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "\u0412\u044b\u0431\u0440\u0430\u0442\u044c \u043b\u043e\u0433\u043e\u0442\u0438\u043f \u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u0438", "", "\u0418\u0437\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u0438\u044f (*.png *.svg *.jpg)"
        )
        if path:
            self._org_logo_label.setText(path)

    def _add_org_jury_row(self) -> None:
        row = self._org_jury_table.rowCount()
        self._org_jury_table.insertRow(row)
        for col in range(4):
            self._org_jury_table.setItem(row, col, QTableWidgetItem(""))

    def _remove_org_jury_row(self) -> None:
        row = self._org_jury_table.currentRow()
        if row >= 0:
            self._org_jury_table.removeRow(row)

    def _save_organization_profile(self) -> None:
        jury_members: list[dict[str, str]] = []
        for row_idx in range(self._org_jury_table.rowCount()):
            position = (self._org_jury_table.item(row_idx, 0) or QTableWidgetItem("")).text()
            name = (self._org_jury_table.item(row_idx, 1) or QTableWidgetItem("")).text()
            category = (self._org_jury_table.item(row_idx, 2) or QTableWidgetItem("")).text()
            city = (self._org_jury_table.item(row_idx, 3) or QTableWidgetItem("")).text()
            if position or name:
                jury_members.append({"position": position, "name": name, "category": category, "city": city})

        logo_text = self._org_logo_label.text()
        logo_path: str | None = None if logo_text == "\u041d\u0435 \u0432\u044b\u0431\u0440\u0430\u043d" else logo_text

        update_organization_profile({
            "org_name": self._org_name_edit.toPlainText(),
            "city": self._org_city_edit.text(),
            "default_venue": self._org_venue_edit.text(),
            "logo_path": logo_path,
            "jury_members": jury_members,
        })
        QMessageBox.information(self, "\u041e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u044f", "\u041f\u0440\u043e\u0444\u0438\u043b\u044c \u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u0438 \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d.")

    def _build_profile_group(self) -> QGroupBox:
        group = QGroupBox("Профили", self)
        layout = QVBoxLayout(group)

        paths = get_runtime_paths()
        profile_name = paths.profile_root.name
        profile_path = str(paths.profile_root)

        info_label = QLabel(
            f"Текущий профиль: <b>{profile_name}</b><br>"
            f"Путь: {profile_path}",
            group,
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        manage_btn = QPushButton("Управление профилями", group)
        manage_btn.setToolTip("Открыть диалог управления профилями")
        manage_btn.clicked.connect(self._open_profile_manager)
        layout.addWidget(manage_btn)

        return group

    def _open_profile_manager(self) -> None:
        base_dir = get_profiles_base_dir()
        manager = ProfileManager(base_dir)
        dialog = ProfileSelectorDialog(manager, self)
        dialog.exec()

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

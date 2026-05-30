"""Sidebar navigation widget for the Darts Liga application."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class _NavItem(QPushButton):
    """A single navigation item button."""

    def __init__(self, key: str, label: str, icon: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.key = key
        self._label_text = label
        self._icon_text = icon
        self.setCheckable(True)
        self.setFlat(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName(f"nav_item_{key}")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(32)
        self._update_text(expanded=True)

    def _update_text(self, *, expanded: bool) -> None:
        if expanded:
            self.setText(f"  {self._icon_text}  {self._label_text}")
            self.setToolTip("")
        else:
            self.setText(f" {self._icon_text}")
            self.setToolTip(self._label_text)


class _NavGroup(QWidget):
    """A collapsible group of navigation items."""

    item_clicked = Signal(str)

    def __init__(self, title: str, icon: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title_text = title
        self._icon_text = icon
        self._expanded_mode = True
        self._collapsed_group = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._header = QPushButton(self)
        self._header.setFlat(True)
        self._header.setObjectName(f"nav_group_header_{title}")
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._header.setMinimumHeight(36)
        self._header.clicked.connect(self._toggle_group)
        layout.addWidget(self._header)

        self._items_container = QWidget(self)
        self._items_layout = QVBoxLayout(self._items_container)
        self._items_layout.setContentsMargins(8, 0, 0, 0)
        self._items_layout.setSpacing(0)
        layout.addWidget(self._items_container)

        self._items: list[_NavItem] = []
        self._update_header()

    def add_item(self, key: str, label: str, icon: str) -> _NavItem:
        item = _NavItem(key, label, icon, self._items_container)
        item.clicked.connect(lambda: self.item_clicked.emit(key))
        self._items_layout.addWidget(item)
        self._items.append(item)
        return item

    def items(self) -> list[_NavItem]:
        return list(self._items)

    def set_sidebar_expanded(self, expanded: bool) -> None:
        self._expanded_mode = expanded
        self._update_header()
        for item in self._items:
            item._update_text(expanded=expanded)
        if not expanded:
            self._items_container.hide()
        elif not self._collapsed_group:
            self._items_container.show()

    def _toggle_group(self) -> None:
        self._collapsed_group = not self._collapsed_group
        if self._collapsed_group:
            self._items_container.hide()
        else:
            self._items_container.show()
        self._update_header()

    def _update_header(self) -> None:
        arrow = "\u25B8" if self._collapsed_group else "\u25BE"
        if self._expanded_mode:
            self._header.setText(f" {self._icon_text} {self._title_text} {arrow}")
            self._header.setToolTip("")
        else:
            self._header.setText(f" {self._icon_text}")
            self._header.setToolTip(self._title_text)

    def set_group_expanded(self, expanded: bool) -> None:
        self._collapsed_group = not expanded
        if self._collapsed_group:
            self._items_container.hide()
        else:
            self._items_container.show()
        self._update_header()


class SidebarWidget(QWidget):
    """Sidebar navigation panel with collapsible groups and items."""

    navigation_changed = Signal(str)

    # Navigation structure: group_key -> (group_title, group_icon, [(item_key, item_label, item_icon)])
    NAV_STRUCTURE: list[tuple[str, str, str, list[tuple[str, str, str]]]] = [
        ("glavnaya", "Главная", "\U0001F3E0", [
            ("dashboard", "Главная", "\U0001F3E0"),
        ]),
        ("rabota", "Работа", "\U0001F4CB", [
            ("rating", "Рейтинг", "\u2B50"),
            ("tournaments", "Турниры", "\U0001F3C6"),
            ("players", "Игроки", "\U0001F465"),
        ]),
        ("trener", "Тренер", "\U0001F393", [
            ("coach", "Задачи", "\U0001F4DD"),
            ("analytics", "Аналитика", "\U0001F4CA"),
            ("context", "Контекст", "\U0001F4D6"),
        ]),
        ("dannye", "Данные", "\U0001F4C1", [
            ("import_export", "Импорт/Экспорт", "\U0001F4E5"),
            ("reports", "Отчеты", "\U0001F4C4"),
        ]),
        ("sistema", "Система", "\u2699", [
            ("diagnostics", "Диагностика", "\U0001F527"),
            ("settings", "Настройки", "\u2699"),
            ("faq", "Справка", "\u2753"),
            ("about", "О программе", "\u2139"),
        ]),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar_widget")
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self._is_expanded = True
        self.setFixedWidth(180)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 8, 4, 8)
        main_layout.setSpacing(4)

        # Branding
        self._branding_label = QLabel("\U0001F3AF Дартс Лига", self)
        self._branding_label.setObjectName("sidebar_branding")
        self._branding_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._branding_label.setMinimumHeight(40)
        main_layout.addWidget(self._branding_label)

        # Separator
        sep = QFrame(self)
        sep.setFrameShape(QFrame.Shape.HLine)
        main_layout.addWidget(sep)

        # Scrollable navigation area
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        nav_container = QWidget()
        self._nav_layout = QVBoxLayout(nav_container)
        self._nav_layout.setContentsMargins(0, 4, 0, 4)
        self._nav_layout.setSpacing(2)

        self._groups: list[_NavGroup] = []
        self._all_items: dict[str, _NavItem] = {}
        self._group_map: dict[str, _NavGroup] = {}

        for group_key, group_title, group_icon, items in self.NAV_STRUCTURE:
            group = _NavGroup(group_title, group_icon, nav_container)
            group.item_clicked.connect(self._on_item_clicked)
            self._nav_layout.addWidget(group)
            self._groups.append(group)
            self._group_map[group_key] = group
            for item_key, item_label, item_icon in items:
                nav_item = group.add_item(item_key, item_label, item_icon)
                self._all_items[item_key] = nav_item

        self._nav_layout.addStretch(1)
        scroll.setWidget(nav_container)
        main_layout.addWidget(scroll, 1)

        # Collapse button
        self._collapse_btn = QPushButton("\u25C0 Свернуть", self)
        self._collapse_btn.setObjectName("sidebar_collapse_btn")
        self._collapse_btn.setFlat(True)
        self._collapse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._collapse_btn.clicked.connect(self.toggle_collapsed)
        main_layout.addWidget(self._collapse_btn)

        self._current_item: str = "dashboard"
        self._update_active_state()

    def _on_item_clicked(self, key: str) -> None:
        if key != self._current_item:
            self._current_item = key
            self._update_active_state()
            self.navigation_changed.emit(key)

    def _update_active_state(self) -> None:
        for item_key, item in self._all_items.items():
            item.setChecked(item_key == self._current_item)

    def set_current_item(self, key: str) -> None:
        if key in self._all_items and key != self._current_item:
            self._current_item = key
            self._update_active_state()

    def current_item(self) -> str:
        return self._current_item

    def toggle_collapsed(self) -> None:
        self._is_expanded = not self._is_expanded
        if self._is_expanded:
            self.setFixedWidth(180)
            self._branding_label.setText("\U0001F3AF Дартс Лига")
            self._collapse_btn.setText("\u25C0 Свернуть")
        else:
            self.setFixedWidth(50)
            self._branding_label.setText("\U0001F3AF")
            self._collapse_btn.setText("\u25B6")
        for group in self._groups:
            group.set_sidebar_expanded(self._is_expanded)

    def is_expanded(self) -> bool:
        return self._is_expanded

    def groups(self) -> list[_NavGroup]:
        return list(self._groups)

    def group_keys(self) -> list[str]:
        return [k for k, _, _, _ in self.NAV_STRUCTURE]

    def items_in_group(self, group_index: int) -> list[str]:
        if 0 <= group_index < len(self._groups):
            return [item.key for item in self._groups[group_index].items()]
        return []

    def activate_group(self, group_index: int) -> None:
        """Activate the first item in a group by index."""
        items = self.items_in_group(group_index)
        if items:
            self._on_item_clicked(items[0])

    def activate_sub_item(self, group_index: int, sub_index: int) -> None:
        """Activate a specific sub-item within a group."""
        items = self.items_in_group(group_index)
        if 0 <= sub_index < len(items):
            self._on_item_clicked(items[sub_index])

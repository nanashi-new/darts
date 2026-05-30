"""Theme manager for the Darts Liga application."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication


LIGHT_THEME_QSS = """
QWidget {
    background-color: #FFFFFF;
    color: #212121;
    font-family: "Segoe UI", "Noto Sans", sans-serif;
}

QToolTip {
    background-color: #F5F5F5;
    color: #212121;
    border: 1px solid #BDBDBD;
    padding: 4px;
    border-radius: 4px;
}

QPushButton {
    background-color: #1976D2;
    color: #FFFFFF;
    border: none;
    border-radius: 4px;
    padding: 6px 14px;
    min-height: 22px;
}
QPushButton:hover {
    background-color: #1565C0;
}
QPushButton:pressed {
    background-color: #0D47A1;
}
QPushButton:disabled {
    background-color: #BDBDBD;
    color: #757575;
}

QTableWidget, QTableView {
    background-color: #FFFFFF;
    alternate-background-color: #F5F5F5;
    gridline-color: #E0E0E0;
    selection-background-color: #BBDEFB;
    selection-color: #212121;
    border: 1px solid #E0E0E0;
    border-radius: 4px;
}
QTableWidget::item:hover, QTableView::item:hover {
    background-color: #E3F2FD;
}
QHeaderView::section {
    background-color: #F5F5F5;
    color: #212121;
    padding: 4px;
    border: 1px solid #E0E0E0;
}

QTabWidget::pane {
    border: 1px solid #E0E0E0;
    border-radius: 4px;
}
QTabBar::tab {
    background-color: #F5F5F5;
    color: #616161;
    padding: 6px 12px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #1976D2;
    border-bottom: 2px solid #1976D2;
}

QScrollArea {
    border: none;
    background-color: #FFFFFF;
}

QGroupBox {
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 16px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 4px;
    color: #424242;
}

QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #BDBDBD;
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 22px;
}
QComboBox:hover {
    border-color: #1976D2;
}
QComboBox::drop-down {
    border: none;
}

QLineEdit {
    background-color: #FFFFFF;
    border: 1px solid #BDBDBD;
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 22px;
}
QLineEdit:focus {
    border-color: #1976D2;
}

QTextEdit {
    background-color: #FFFFFF;
    border: 1px solid #BDBDBD;
    border-radius: 4px;
    padding: 4px;
}
QTextEdit:focus {
    border-color: #1976D2;
}

QDialog {
    background-color: #FFFFFF;
}

QMessageBox {
    background-color: #FFFFFF;
}

QLabel {
    background-color: transparent;
    border: none;
}

QStatusBar {
    background-color: #F5F5F5;
    color: #616161;
    border-top: 1px solid #E0E0E0;
}

QSpinBox {
    background-color: #FFFFFF;
    border: 1px solid #BDBDBD;
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 22px;
}

QSplitter::handle {
    background-color: #E0E0E0;
}

/* Sidebar styles - light theme */
#sidebar_widget {
    background-color: #F0F0F0;
    border-right: 1px solid #E0E0E0;
}
#sidebar_branding {
    font-size: 14px;
    font-weight: bold;
    color: #1976D2;
}
#sidebar_widget QPushButton {
    background-color: transparent;
    color: #424242;
    text-align: left;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
}
#sidebar_widget QPushButton:hover {
    background-color: #E0E0E0;
}
#sidebar_widget QPushButton:checked {
    background-color: #BBDEFB;
    color: #1976D2;
    font-weight: bold;
}
#sidebar_collapse_btn {
    background-color: transparent;
    color: #757575;
    border-top: 1px solid #E0E0E0;
    border-radius: 0px;
    padding: 6px;
}
#sidebar_collapse_btn:hover {
    background-color: #E0E0E0;
}
"""

DARK_THEME_QSS = """
QWidget {
    background-color: #19232D;
    color: #DFE1E2;
    font-family: "Segoe UI", "Noto Sans", sans-serif;
}

QToolTip {
    background-color: #1E2A36;
    color: #DFE1E2;
    border: 1px solid #346792;
    padding: 4px;
    border-radius: 4px;
}

QPushButton {
    background-color: #346792;
    color: #DFE1E2;
    border: none;
    border-radius: 4px;
    padding: 6px 14px;
    min-height: 22px;
}
QPushButton:hover {
    background-color: #3D7AB5;
}
QPushButton:pressed {
    background-color: #255078;
}
QPushButton:disabled {
    background-color: #2D3843;
    color: #6B7B8D;
}

QTableWidget, QTableView {
    background-color: #19232D;
    alternate-background-color: #1E2A36;
    gridline-color: #2D3843;
    selection-background-color: #346792;
    selection-color: #DFE1E2;
    border: 1px solid #2D3843;
    border-radius: 4px;
}
QTableWidget::item:hover, QTableView::item:hover {
    background-color: #253545;
}
QHeaderView::section {
    background-color: #1E2A36;
    color: #DFE1E2;
    padding: 4px;
    border: 1px solid #2D3843;
}

QTabWidget::pane {
    border: 1px solid #2D3843;
    border-radius: 4px;
}
QTabBar::tab {
    background-color: #1E2A36;
    color: #8B9DAF;
    padding: 6px 12px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #19232D;
    color: #54A3D8;
    border-bottom: 2px solid #346792;
}

QScrollArea {
    border: none;
    background-color: #19232D;
}

QGroupBox {
    border: 1px solid #2D3843;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 16px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 4px;
    color: #8B9DAF;
}

QComboBox {
    background-color: #1E2A36;
    border: 1px solid #2D3843;
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 22px;
    color: #DFE1E2;
}
QComboBox:hover {
    border-color: #346792;
}
QComboBox::drop-down {
    border: none;
}

QLineEdit {
    background-color: #1E2A36;
    border: 1px solid #2D3843;
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 22px;
    color: #DFE1E2;
}
QLineEdit:focus {
    border-color: #346792;
}

QTextEdit {
    background-color: #1E2A36;
    border: 1px solid #2D3843;
    border-radius: 4px;
    padding: 4px;
    color: #DFE1E2;
}
QTextEdit:focus {
    border-color: #346792;
}

QDialog {
    background-color: #19232D;
}

QMessageBox {
    background-color: #19232D;
}

QLabel {
    background-color: transparent;
    border: none;
}

QStatusBar {
    background-color: #1E2A36;
    color: #8B9DAF;
    border-top: 1px solid #2D3843;
}

QSpinBox {
    background-color: #1E2A36;
    border: 1px solid #2D3843;
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 22px;
    color: #DFE1E2;
}

QSplitter::handle {
    background-color: #2D3843;
}

/* Sidebar styles - dark theme */
#sidebar_widget {
    background-color: #151D25;
    border-right: 1px solid #2D3843;
}
#sidebar_branding {
    font-size: 14px;
    font-weight: bold;
    color: #54A3D8;
}
#sidebar_widget QPushButton {
    background-color: transparent;
    color: #8B9DAF;
    text-align: left;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
}
#sidebar_widget QPushButton:hover {
    background-color: #253545;
}
#sidebar_widget QPushButton:checked {
    background-color: #253545;
    color: #54A3D8;
    font-weight: bold;
}
#sidebar_collapse_btn {
    background-color: transparent;
    color: #6B7B8D;
    border-top: 1px solid #2D3843;
    border-radius: 0px;
    padding: 6px;
}
#sidebar_collapse_btn:hover {
    background-color: #253545;
}
"""

_FONT_SIZE_MAP: dict[str, str] = {
    "small": "12px",
    "medium": "14px",
    "large": "16px",
}


class ThemeManager:
    """Manages application themes (light/dark) with QSS stylesheets."""

    @classmethod
    def apply_theme(
        cls,
        app: QApplication,
        theme_name: str,
        accent_color: str = "",
        font_size: str = "medium",
    ) -> None:
        """Apply a named theme to the application."""
        if theme_name == "dark":
            qss = DARK_THEME_QSS
        else:
            qss = LIGHT_THEME_QSS

        size = _FONT_SIZE_MAP.get(font_size, _FONT_SIZE_MAP["medium"])
        qss += f"\nQWidget {{ font-size: {size}; }}\n"

        if accent_color:
            hover_color = cls._lighten_color(accent_color, 20)
            pressed_color = cls._darken_color(accent_color, 20)
            qss += (
                f"\nQPushButton {{ background-color: {accent_color}; }}\n"
                f"QPushButton:hover {{ background-color: {hover_color}; }}\n"
                f"QPushButton:pressed {{ background-color: {pressed_color}; }}\n"
            )

        app.setStyleSheet(qss)

    @classmethod
    def get_available_themes(cls) -> list[str]:
        """Return available theme names."""
        return ["light", "dark"]

    @staticmethod
    def _lighten_color(hex_color: str, amount: int) -> str:
        """Return a lighter shade of the given hex color."""
        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6:
            return f"#{hex_color}"
        r = min(255, int(hex_color[0:2], 16) + amount)
        g = min(255, int(hex_color[2:4], 16) + amount)
        b = min(255, int(hex_color[4:6], 16) + amount)
        return f"#{r:02X}{g:02X}{b:02X}"

    @staticmethod
    def _darken_color(hex_color: str, amount: int) -> str:
        """Return a darker shade of the given hex color."""
        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6:
            return f"#{hex_color}"
        r = max(0, int(hex_color[0:2], 16) - amount)
        g = max(0, int(hex_color[2:4], 16) - amount)
        b = max(0, int(hex_color[4:6], 16) - amount)
        return f"#{r:02X}{g:02X}{b:02X}"

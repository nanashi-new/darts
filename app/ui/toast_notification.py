"""Non-blocking toast notification widget."""

from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QLabel, QWidget


class ToastNotification(QLabel):
    """Non-blocking notification that auto-hides after 3 seconds."""

    _STYLE_MAP: dict[str, str] = {
        "info": "background-color: rgba(46, 125, 50, 200); color: white;",
        "warning": "background-color: rgba(237, 201, 0, 200); color: black;",
        "error": "background-color: rgba(198, 40, 40, 200); color: white;",
    }

    def __init__(self, parent: QWidget, message: str, level: str = "info") -> None:
        super().__init__(message, parent)
        self.setObjectName("toast_notification")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.setFixedWidth(320)

        base_style = self._STYLE_MAP.get(level, self._STYLE_MAP["info"])
        self.setStyleSheet(
            f"{base_style} border-radius: 8px; padding: 12px 16px; font-size: 13px;"
        )

        self._position_at_bottom_right(parent)
        QTimer.singleShot(3000, self._auto_hide)

    def _position_at_bottom_right(self, parent: QWidget) -> None:
        parent_rect = parent.rect()
        x = parent_rect.width() - self.width() - 20
        y = parent_rect.height() - 80
        self.move(x, y)

    def _auto_hide(self) -> None:
        self.hide()
        self.deleteLater()

    @staticmethod
    def show_toast(
        parent: QWidget, message: str, level: str = "info"
    ) -> "ToastNotification":
        """Create, position, show, and return a toast notification instance."""
        toast = ToastNotification(parent, message, level)
        toast.show()
        toast.raise_()
        return toast

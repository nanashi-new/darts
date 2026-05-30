"""Guided tour overlay that walks users through key UI elements."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.settings import load_settings, update_setting

_SETTINGS_KEY = "guided_tour_completed"

# Tour completion is stored per-profile intentionally. Each profile represents a
# separate user context (potentially a different person), so the tour replays
# when a new profile is created or switched to.


@dataclass(frozen=True)
class TourStep:
    """Single step of a guided tour."""

    target_name: str
    text: str


DEFAULT_STEPS: list[TourStep] = [
    TourStep(
        target_name="sidebar_widget",
        text="Используйте боковую панель для навигации между разделами приложения.",
    ),
    TourStep(
        target_name="sidebar_widget",
        text="Раздел «Данные» содержит импорт/экспорт результатов турниров из файлов.",
    ),
    TourStep(
        target_name="sidebar_widget",
        text="Раздел «Работа» содержит рейтинг игроков, турниры и список участников.",
    ),
    TourStep(
        target_name="sidebar_widget",
        text="Раздел «Тренер» содержит задачи, аналитику и контекст.",
    ),
    TourStep(
        target_name="sidebar_widget",
        text="Раздел «Система» содержит диагностику, настройки и справку.",
    ),
    TourStep(
        target_name="sidebar_widget",
        text="Боковую панель можно свернуть кнопкой внизу для увеличения рабочей области.",
    ),
]


class GuidedTour(QWidget):
    """Overlay widget that displays step-by-step tour."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self._steps = list(DEFAULT_STEPS)
        self._current_index = 0

        self.setObjectName("guided_tour_overlay")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()

        self._frame = QFrame(self)
        self._frame.setObjectName("guided_tour_frame")
        self._frame.setStyleSheet(
            "QFrame#guided_tour_frame {"
            "  background-color: #1976D2;"
            "  border-radius: 8px;"
            "  padding: 16px;"
            "}"
        )
        frame_layout = QVBoxLayout(self._frame)

        self._text_label = QLabel(self)
        self._text_label.setWordWrap(True)
        self._text_label.setStyleSheet("color: white; font-size: 14px;")
        frame_layout.addWidget(self._text_label)

        self._step_label = QLabel(self)
        self._step_label.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 12px;")
        frame_layout.addWidget(self._step_label)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self._skip_btn = QPushButton("Пропустить")
        self._skip_btn.setObjectName("tour_skip_btn")
        self._skip_btn.clicked.connect(self.skip_tour)
        buttons_layout.addWidget(self._skip_btn)

        self._next_btn = QPushButton("Далее")
        self._next_btn.setObjectName("tour_next_btn")
        self._next_btn.clicked.connect(self.next_step)
        buttons_layout.addWidget(self._next_btn)

        frame_layout.addLayout(buttons_layout)
        layout.addWidget(self._frame)

        self.hide()

    @property
    def steps(self) -> list[TourStep]:
        """Return the list of tour steps."""
        return list(self._steps)

    def start_tour(self) -> None:
        """Show first step of the tour."""
        self._current_index = 0
        self._show_current_step()
        self.show()
        self.raise_()

    def next_step(self) -> None:
        """Advance to next step or finish the tour."""
        self._current_index += 1
        if self._current_index >= len(self._steps):
            self._finish_tour()
        else:
            self._show_current_step()

    def skip_tour(self) -> None:
        """Skip remaining steps and mark tour as completed."""
        self._finish_tour()

    def _finish_tour(self) -> None:
        """Mark tour completed and hide overlay."""
        mark_completed()
        self.hide()

    def _show_current_step(self) -> None:
        """Display the current step text and counter."""
        step = self._steps[self._current_index]
        self._text_label.setText(step.text)
        self._step_label.setText(
            f"Шаг {self._current_index + 1} из {len(self._steps)}"
        )
        if self._current_index == len(self._steps) - 1:
            self._next_btn.setText("Завершить")
        else:
            self._next_btn.setText("Далее")


def is_tour_completed() -> bool:
    """Check if the guided tour has been completed."""
    settings = load_settings()
    return bool(settings.get(_SETTINGS_KEY, False))


def mark_completed() -> None:
    """Mark the guided tour as completed in settings."""
    update_setting(_SETTINGS_KEY, True)

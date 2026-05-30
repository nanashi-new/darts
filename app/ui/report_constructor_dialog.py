"""Report constructor dialog for building configurable reports."""

from __future__ import annotations

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.services.report_builder import ReportConfig


class ReportConstructorDialog(QDialog):
    """Dialog for constructing a custom report."""

    def __init__(self, leagues: list[str], categories: list[str], parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(parent)
        self.setWindowTitle("Конструктор отчета")
        self.setMinimumWidth(420)
        self._build_accepted = False

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Разделы отчета:"))
        self._cb_rating = QCheckBox("Рейтинг")
        self._cb_rating.setChecked(True)
        layout.addWidget(self._cb_rating)
        self._cb_tournaments = QCheckBox("Турниры")
        layout.addWidget(self._cb_tournaments)
        self._cb_players = QCheckBox("Игроки")
        layout.addWidget(self._cb_players)
        self._cb_analytics = QCheckBox("Аналитика")
        layout.addWidget(self._cb_analytics)

        self._cb_all_dates = QCheckBox("Все даты")
        self._cb_all_dates.setChecked(True)
        self._cb_all_dates.toggled.connect(self._toggle_dates)
        layout.addWidget(self._cb_all_dates)

        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("С:"))
        self._date_start = QDateEdit()
        self._date_start.setCalendarPopup(True)
        self._date_start.setDate(QDate.currentDate().addYears(-1))
        self._date_start.setEnabled(False)
        date_layout.addWidget(self._date_start)
        date_layout.addWidget(QLabel("По:"))
        self._date_end = QDateEdit()
        self._date_end.setCalendarPopup(True)
        self._date_end.setDate(QDate.currentDate())
        self._date_end.setEnabled(False)
        date_layout.addWidget(self._date_end)
        layout.addLayout(date_layout)

        layout.addWidget(QLabel("Лига:"))
        self._league_combo = QComboBox()
        self._league_combo.addItem("Все", "")
        for code in leagues:
            self._league_combo.addItem(code, code)
        layout.addWidget(self._league_combo)

        layout.addWidget(QLabel("Категория:"))
        self._category_combo = QComboBox()
        self._category_combo.addItem("Все", "")
        for code in categories:
            self._category_combo.addItem(code, code)
        layout.addWidget(self._category_combo)

        layout.addWidget(QLabel("Формат:"))
        self._format_combo = QComboBox()
        self._format_combo.addItems(["Текст", "XLSX", "PDF"])
        layout.addWidget(self._format_combo)

        btn_layout = QHBoxLayout()
        build_btn = QPushButton("Сформировать")
        build_btn.setToolTip("Сформировать отчет с выбранными параметрами.")
        build_btn.clicked.connect(self._on_build)
        btn_layout.addWidget(build_btn)

        save_template_btn = QPushButton("Сохранить как шаблон")
        save_template_btn.setToolTip("Сохранить текущие настройки как шаблон для повторного использования.")
        save_template_btn.clicked.connect(self._on_save_template)
        btn_layout.addWidget(save_template_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setToolTip("Закрыть без действия.")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self._save_requested = False

    def _toggle_dates(self, checked: bool) -> None:
        self._date_start.setEnabled(not checked)
        self._date_end.setEnabled(not checked)

    def get_config(self) -> ReportConfig:
        sections: list[str] = []
        if self._cb_rating.isChecked():
            sections.append("rating")
        if self._cb_tournaments.isChecked():
            sections.append("tournaments")
        if self._cb_players.isChecked():
            sections.append("players")
        if self._cb_analytics.isChecked():
            sections.append("analytics")

        period_start: str | None = None
        period_end: str | None = None
        if not self._cb_all_dates.isChecked():
            period_start = self._date_start.date().toString("yyyy-MM-dd")
            period_end = self._date_end.date().toString("yyyy-MM-dd")

        league_code: str | None = self._league_combo.currentData() or None
        category_code: str | None = self._category_combo.currentData() or None

        fmt_map = {"Текст": "text", "XLSX": "xlsx", "PDF": "pdf"}
        output_format = fmt_map.get(self._format_combo.currentText(), "text")

        return ReportConfig(
            sections=sections,
            period_start=period_start,
            period_end=period_end,
            league_code=league_code,
            category_code=category_code,
            player_ids=None,
            output_format=output_format,
        )

    def load_config(self, config: ReportConfig) -> None:
        self._cb_rating.setChecked("rating" in config.sections)
        self._cb_tournaments.setChecked("tournaments" in config.sections)
        self._cb_players.setChecked("players" in config.sections)
        self._cb_analytics.setChecked("analytics" in config.sections)

        if config.period_start or config.period_end:
            self._cb_all_dates.setChecked(False)
            if config.period_start:
                self._date_start.setDate(QDate.fromString(config.period_start, "yyyy-MM-dd"))
            if config.period_end:
                self._date_end.setDate(QDate.fromString(config.period_end, "yyyy-MM-dd"))
        else:
            self._cb_all_dates.setChecked(True)

        if config.league_code:
            idx = self._league_combo.findData(config.league_code)
            if idx >= 0:
                self._league_combo.setCurrentIndex(idx)

        if config.category_code:
            idx = self._category_combo.findData(config.category_code)
            if idx >= 0:
                self._category_combo.setCurrentIndex(idx)

        fmt_map = {"text": "Текст", "xlsx": "XLSX", "pdf": "PDF"}
        fmt_text = fmt_map.get(config.output_format, "Текст")
        idx = self._format_combo.findText(fmt_text)
        if idx >= 0:
            self._format_combo.setCurrentIndex(idx)

    def _on_build(self) -> None:
        config = self.get_config()
        if not config.sections:
            QMessageBox.warning(self, "Конструктор отчета", "Выберите хотя бы один раздел.")
            return
        self._build_accepted = True
        self.accept()

    def _on_save_template(self) -> None:
        config = self.get_config()
        if not config.sections:
            QMessageBox.warning(self, "Конструктор отчета", "Выберите хотя бы один раздел.")
            return
        self._save_requested = True
        self.accept()

    @property
    def build_accepted(self) -> bool:
        return self._build_accepted

    @property
    def save_requested(self) -> bool:
        return self._save_requested

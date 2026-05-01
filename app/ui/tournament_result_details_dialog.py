from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class TournamentResultDetailsDialog(QDialog):
    def __init__(self, *, result: dict[str, object], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Детали результата")
        self.resize(520, 520)

        root_layout = QVBoxLayout(self)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        root_layout.addWidget(scroll_area)

        content = QWidget(self)
        scroll_area.setWidget(content)
        form = QFormLayout(content)

        fields = [
            ("fio", "Игрок"),
            ("birth_date", "Дата рождения"),
            ("place", "Место"),
            ("score_set", "Набор очков"),
            ("score_sector20", "Сектор 20"),
            ("score_big_round", "Большой раунд"),
            ("points_place", "Очки за место"),
            ("points_total", "Итого"),
            ("coach", "Тренер"),
            ("club", "Клуб"),
            ("gender", "Пол"),
            ("player_id", "ID игрока"),
            ("result_id", "ID результата"),
            ("tournament_id", "ID турнира"),
            ("calc_version", "Версия расчета"),
        ]
        for key, label in fields:
            value = result.get(key)
            form.addRow(label, self._text(str(value) if value not in (None, "") else "-"))

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        if close_button := buttons.button(QDialogButtonBox.StandardButton.Close):
            close_button.setText("Закрыть")
        buttons.rejected.connect(self.reject)
        root_layout.addWidget(buttons)

    def _text(self, value: str) -> QLabel:
        label = QLabel(value, self)
        label.setWordWrap(True)
        return label

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
)


@dataclass(frozen=True)
class PlayerFormData:
    last_name: str
    first_name: str
    middle_name: str | None
    birth_date: str | None
    gender: str | None
    coach: str | None
    club: str | None
    notes: str | None


class PlayerEditDialog(QDialog):
    def __init__(self, parent=None, player: dict[str, object] | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Новый игрок" if player is None else "Редактировать игрока")
        self.resize(480, 420)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.last_name_input = QLineEdit(self)
        self.first_name_input = QLineEdit(self)
        self.middle_name_input = QLineEdit(self)
        self.birth_date_input = QLineEdit(self)
        self.birth_date_input.setPlaceholderText("YYYY-MM-DD")

        self.gender_combo = QComboBox(self)
        self.gender_combo.addItem("—", None)
        self.gender_combo.addItem("M", "M")
        self.gender_combo.addItem("F", "F")

        self.coach_input = QLineEdit(self)
        self.club_input = QLineEdit(self)
        self.notes_input = QTextEdit(self)
        self.notes_input.setMinimumHeight(90)

        form.addRow("Фамилия*", self.last_name_input)
        form.addRow("Имя*", self.first_name_input)
        form.addRow("Отчество", self.middle_name_input)
        form.addRow("Дата рождения", self.birth_date_input)
        form.addRow("Пол", self.gender_combo)
        form.addRow("Тренер", self.coach_input)
        form.addRow("Клуб", self.club_input)
        form.addRow("Примечания", self.notes_input)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.accepted.connect(self._accept_if_valid)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if player is not None:
            self._fill(player)

    def _fill(self, player: dict[str, object]) -> None:
        self.last_name_input.setText(str(player.get("last_name") or ""))
        self.first_name_input.setText(str(player.get("first_name") or ""))
        self.middle_name_input.setText(str(player.get("middle_name") or ""))
        self.birth_date_input.setText(str(player.get("birth_date") or ""))
        self.coach_input.setText(str(player.get("coach") or ""))
        self.club_input.setText(str(player.get("club") or ""))
        self.notes_input.setPlainText(str(player.get("notes") or ""))

        gender = str(player.get("gender") or "")
        index = self.gender_combo.findData(gender if gender in {"M", "F"} else None)
        self.gender_combo.setCurrentIndex(index if index >= 0 else 0)

    def _accept_if_valid(self) -> None:
        if not self.last_name_input.text().strip() or not self.first_name_input.text().strip():
            QMessageBox.warning(self, "Игрок", "Поля Фамилия и Имя обязательны.")
            return
        self.accept()

    def form_data(self) -> PlayerFormData:
        def _optional(text: str) -> str | None:
            value = text.strip()
            return value or None

        return PlayerFormData(
            last_name=self.last_name_input.text().strip(),
            first_name=self.first_name_input.text().strip(),
            middle_name=_optional(self.middle_name_input.text()),
            birth_date=_optional(self.birth_date_input.text()),
            gender=self.gender_combo.currentData(),
            coach=_optional(self.coach_input.text()),
            club=_optional(self.club_input.text()),
            notes=_optional(self.notes_input.toPlainText()),
        )

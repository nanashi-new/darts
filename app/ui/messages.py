from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget


def confirm_yes_no(parent: QWidget, title: str, text: str) -> bool:
    message_box = QMessageBox(parent)
    message_box.setIcon(QMessageBox.Icon.Question)
    message_box.setWindowTitle(title)
    message_box.setText(text)
    yes_button = message_box.addButton("Да", QMessageBox.ButtonRole.YesRole)
    message_box.addButton("Нет", QMessageBox.ButtonRole.NoRole)
    message_box.setDefaultButton(yes_button)
    message_box.exec()
    return message_box.clickedButton() is yes_button

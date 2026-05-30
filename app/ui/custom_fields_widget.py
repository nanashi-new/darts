"""Custom fields widget for player card."""
from __future__ import annotations

import sqlite3

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.services.custom_fields import (
    CustomFieldRecord,
    create_custom_field,
    delete_custom_field,
    get_player_custom_values,
    list_custom_fields,
    set_field_value,
)


class ManageFieldsDialog(QDialog):
    """Dialog to create/delete custom field definitions."""

    def __init__(self, *, connection: sqlite3.Connection, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._connection = connection
        self.setWindowTitle("Управление полями")
        self.resize(400, 300)

        layout = QVBoxLayout(self)

        # Existing fields list
        self._fields_layout = QVBoxLayout()
        layout.addLayout(self._fields_layout)

        # New field form
        layout.addWidget(QLabel("Создать новое поле:"))
        form_row = QHBoxLayout()
        self._name_edit = QLineEdit(self)
        self._name_edit.setPlaceholderText("Название")
        form_row.addWidget(self._name_edit)
        self._type_edit = QLineEdit(self)
        self._type_edit.setPlaceholderText("Тип (text/number/date/select)")
        self._type_edit.setText("text")
        form_row.addWidget(self._type_edit)
        self._create_button = QPushButton("Создать")
        self._create_button.clicked.connect(self._on_create)
        form_row.addWidget(self._create_button)
        layout.addLayout(form_row)

        # Close button
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._refresh_fields()

    def _refresh_fields(self) -> None:
        # Clear layout
        while self._fields_layout.count():
            item = self._fields_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        fields = list_custom_fields(self._connection, active_only=False)
        if not fields:
            self._fields_layout.addWidget(QLabel("Нет полей"))
            return

        for field in fields:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.addWidget(QLabel(f"{field.name} ({field.field_type})"))
            row_layout.addStretch(1)
            del_btn = QPushButton("Удалить")
            del_btn.clicked.connect(lambda _checked=False, f=field: self._on_delete(f))
            row_layout.addWidget(del_btn)
            self._fields_layout.addWidget(row_widget)

    def _on_create(self) -> None:
        name = self._name_edit.text().strip()
        field_type = self._type_edit.text().strip() or "text"
        if not name:
            return
        try:
            create_custom_field(self._connection, name, field_type)
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Не удалось создать поле.")
            return
        self._name_edit.clear()
        self._refresh_fields()

    def _on_delete(self, field: CustomFieldRecord) -> None:
        reply = QMessageBox.question(
            self,
            "Удалить поле",
            f"Удалить поле '{field.name}'? Все значения будут потеряны.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_custom_field(self._connection, field.id)
            self._refresh_fields()


class CustomFieldsWidget(QWidget):
    """Reusable widget showing custom field values for a player."""

    def __init__(
        self,
        *,
        connection: sqlite3.Connection,
        player_id: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._connection = connection
        self._player_id = player_id
        self._field_edits: dict[int, QLineEdit] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Form area
        self._form_layout = QFormLayout()
        layout.addLayout(self._form_layout)

        # Buttons
        btn_row = QHBoxLayout()
        self._save_button = QPushButton("Сохранить")
        self._save_button.clicked.connect(self._on_save)
        btn_row.addWidget(self._save_button)

        self._manage_button = QPushButton("Управление полями")
        self._manage_button.clicked.connect(self._on_manage)
        btn_row.addWidget(self._manage_button)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        self._refresh()

    def _refresh(self) -> None:
        # Clear form
        while self._form_layout.rowCount():
            self._form_layout.removeRow(0)
        self._field_edits.clear()

        fields = list_custom_fields(self._connection, active_only=True)
        values = get_player_custom_values(self._connection, self._player_id)
        value_map = {v.field_id: v.value for v in values}

        if not fields:
            self._form_layout.addRow(QLabel("Нет кастомных полей"))
            return

        for field in fields:
            edit = QLineEdit(self)
            current_value = value_map.get(field.id, "")
            edit.setText(current_value or "")
            edit.setPlaceholderText(f"{field.field_type}")
            self._field_edits[field.id] = edit
            self._form_layout.addRow(f"{field.name}:", edit)

    def _on_save(self) -> None:
        for field_id, edit in self._field_edits.items():
            value = edit.text().strip() or None
            set_field_value(self._connection, field_id, self._player_id, value)

    def _on_manage(self) -> None:
        dialog = ManageFieldsDialog(connection=self._connection, parent=self)
        dialog.exec()
        self._refresh()

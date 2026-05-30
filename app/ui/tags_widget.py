"""Tags widget for entity tag management."""
from __future__ import annotations

import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.services.tags import (
    TagRecord,
    assign_tag,
    create_tag,
    list_entity_tags,
    list_tags,
    remove_tag_assignment,
)


class AddTagDialog(QDialog):
    """Dialog to pick an existing tag or create a new one."""

    def __init__(self, *, connection: sqlite3.Connection, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._connection = connection
        self.setWindowTitle("Добавить тег")
        self.resize(350, 160)

        layout = QVBoxLayout(self)

        # Existing tags combo
        layout.addWidget(QLabel("Выбрать существующий:"))
        self._tag_combo = QComboBox(self)
        self._refresh_combo()
        layout.addWidget(self._tag_combo)

        # New tag input
        layout.addWidget(QLabel("Или создать новый:"))
        new_row = QHBoxLayout()
        self._name_edit = QLineEdit(self)
        self._name_edit.setPlaceholderText("Название тега")
        new_row.addWidget(self._name_edit)
        self._color_edit = QLineEdit(self)
        self._color_edit.setPlaceholderText("#FF0000")
        self._color_edit.setMaximumWidth(90)
        new_row.addWidget(self._color_edit)
        layout.addLayout(new_row)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _refresh_combo(self) -> None:
        self._tag_combo.clear()
        self._tag_combo.addItem("-- нет --", None)
        for tag in list_tags(self._connection):
            self._tag_combo.addItem(tag.name, tag.id)

    def selected_tag_id(self) -> int | None:
        """Return selected or newly created tag ID, or None."""
        new_name = self._name_edit.text().strip()
        if new_name:
            try:
                return create_tag(self._connection, new_name, self._color_edit.text().strip() or None)
            except Exception:
                QMessageBox.warning(self, "Ошибка", "Тег с таким именем уже существует.")
                return None
        tag_id = self._tag_combo.currentData()
        if tag_id is not None:
            return int(tag_id)
        return None


class TagsWidget(QWidget):
    """Reusable widget for displaying and managing tags on an entity."""

    def __init__(
        self,
        *,
        connection: sqlite3.Connection,
        entity_type: str,
        entity_id: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._connection = connection
        self._entity_type = entity_type
        self._entity_id = entity_id

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        # Tags row
        self._tags_row = QHBoxLayout()
        self._tags_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._layout.addLayout(self._tags_row)

        # Add button
        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._add_button = QPushButton("Добавить тег")
        self._add_button.clicked.connect(self._on_add_tag)
        btn_row.addWidget(self._add_button)
        self._layout.addLayout(btn_row)

        self._refresh_tags()

    def _refresh_tags(self) -> None:
        # Clear existing tag labels
        while self._tags_row.count():
            item = self._tags_row.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        tags = list_entity_tags(self._connection, self._entity_type, self._entity_id)
        for tag in tags:
            label = self._make_tag_label(tag)
            self._tags_row.addWidget(label)

        if not tags:
            empty_label = QLabel("Нет тегов")
            empty_label.setStyleSheet("color: gray; font-style: italic;")
            self._tags_row.addWidget(empty_label)

    def _make_tag_label(self, tag: TagRecord) -> QLabel:
        color = tag.color or "#5B9BD5"
        label = QLabel(f" {tag.name} \u00d7 ")
        label.setStyleSheet(
            f"background-color: {color}; color: white; border-radius: 3px; padding: 2px 6px;"
        )
        label.setCursor(Qt.CursorShape.PointingHandCursor)
        label.setToolTip(f"Удалить тег: {tag.name}")
        label.mousePressEvent = lambda _event, t=tag: self._remove_tag(t)  # type: ignore[assignment]
        return label

    def _on_add_tag(self) -> None:
        dialog = AddTagDialog(connection=self._connection, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        tag_id = dialog.selected_tag_id()
        if tag_id is not None:
            assign_tag(self._connection, tag_id, self._entity_type, self._entity_id)
            self._refresh_tags()

    def _remove_tag(self, tag: TagRecord) -> None:
        remove_tag_assignment(self._connection, tag.id, self._entity_type, self._entity_id)
        self._refresh_tags()

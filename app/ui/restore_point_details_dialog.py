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

from app.services.restore_points import RestorePointRecord


class RestorePointDetailsDialog(QDialog):
    def __init__(self, *, record: RestorePointRecord, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Детали точки восстановления")
        self.resize(560, 420)

        root_layout = QVBoxLayout(self)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        root_layout.addWidget(scroll_area)

        content = QWidget(self)
        scroll_area.setWidget(content)
        form = QFormLayout(content)

        fields = [
            ("ID", record.id),
            ("Название", record.title),
            ("Причина", record.reason),
            ("Файл", record.file_path),
            ("Источник", record.source),
            ("Операция", record.operation_group_id),
            ("Создано", record.created_at),
        ]
        for label, value in fields:
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

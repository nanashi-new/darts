from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.services.audit_log import AuditLogService, EVENT_TYPES


class AuditLogDialog(QDialog):
    def __init__(self, audit_log_service: AuditLogService, parent=None) -> None:
        super().__init__(parent)
        self._audit_log_service = audit_log_service
        self.setWindowTitle("Журнал операций")
        self.resize(800, 500)

        layout = QVBoxLayout(self)

        filter_row = QHBoxLayout()
        self._type_filter = QComboBox(self)
        self._type_filter.addItem("Все типы", "")
        for event_type in EVENT_TYPES:
            self._type_filter.addItem(event_type, event_type)
        self._type_filter.currentIndexChanged.connect(self._refresh)

        self._search_input = QLineEdit(self)
        self._search_input.setPlaceholderText("Поиск по заголовку и деталям")
        self._search_input.textChanged.connect(self._refresh)

        filter_row.addWidget(QLabel("Тип:", self))
        filter_row.addWidget(self._type_filter)
        filter_row.addWidget(self._search_input)
        layout.addLayout(filter_row)

        self._list_widget = QListWidget(self)
        layout.addWidget(self._list_widget)

        buttons_row = QHBoxLayout()
        export_btn = QPushButton("Экспорт лога в TXT", self)
        export_btn.clicked.connect(self._export_log)
        close_btn = QPushButton("Закрыть", self)
        close_btn.clicked.connect(self.accept)

        buttons_row.addWidget(export_btn)
        buttons_row.addStretch(1)
        buttons_row.addWidget(close_btn)
        layout.addLayout(buttons_row)

        self._refresh()

    def _refresh(self) -> None:
        self._list_widget.clear()
        events = self._audit_log_service.list_events(
            event_type=self._selected_event_type(),
            query=self._search_input.text().strip(),
        )
        for event in events:
            self._list_widget.addItem(
                f"[{event.created_at}] {event.level.upper()} {event.event_type} — {event.title}\n{event.details}"
            )

    def _selected_event_type(self) -> str | None:
        value = self._type_filter.currentData()
        return str(value) if value else None

    def _export_log(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт лога",
            "audit_log.txt",
            "Text Files (*.txt)",
        )
        if not path:
            return

        try:
            exported = self._audit_log_service.export_txt(
                path,
                event_type=self._selected_event_type(),
                query=self._search_input.text().strip(),
            )
        except OSError as exc:
            QMessageBox.critical(self, "Журнал", str(exc))
            return

        QMessageBox.information(self, "Журнал", f"Экспортировано: {exported}")

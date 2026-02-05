from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QLabel,
    QDateEdit,
    QDialog,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.db.database import get_connection
from app.services.import_xlsx import import_tournament_results, parse_first_table_from_xlsx, validate_rows
from app.ui.import_preview_dialog import ImportPreviewDialog


class ImportExportView(QWidget):
    def __init__(self, tournaments_view: QWidget | None = None) -> None:
        super().__init__()
        self._connection = get_connection()
        self._tournaments_view = tournaments_view
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Демо-импорт Excel: выберите файл для предпросмотра."))

        form_layout = QFormLayout()
        self.tournament_name_input = QLineEdit(self)
        self.tournament_name_input.setPlaceholderText("Название турнира")
        form_layout.addRow("Название:", self.tournament_name_input)

        self.tournament_date_input = QDateEdit(self)
        self.tournament_date_input.setCalendarPopup(True)
        self.tournament_date_input.setDate(QDate.currentDate())
        self.tournament_date_input.setDisplayFormat("dd.MM.yyyy")
        form_layout.addRow("Дата:", self.tournament_date_input)

        self.category_code_input = QLineEdit(self)
        self.category_code_input.setPlaceholderText("Например, U12-M")
        form_layout.addRow("Категория:", self.category_code_input)

        layout.addLayout(form_layout)

        self.import_button = QPushButton("Импорт файла (демо)")
        self.import_button.clicked.connect(self._on_import_clicked)
        layout.addWidget(self.import_button)

    def _on_import_clicked(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите XLSX",
            "",
            "Excel файлы (*.xlsx)",
        )
        if not file_path:
            return

        _, rows = parse_first_table_from_xlsx(file_path)
        if not rows:
            QMessageBox.information(
                self,
                "Импорт",
                "Не удалось найти таблицу в файле.",
            )
            return

        warnings = validate_rows(rows)
        dialog = ImportPreviewDialog(rows, warnings, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        tournament_name = self.tournament_name_input.text().strip()
        if not tournament_name:
            QMessageBox.warning(self, "Импорт", "Введите название турнира.")
            return

        tournament_date = self.tournament_date_input.date().toString("yyyy-MM-dd")
        category_code = self.category_code_input.text().strip() or None

        try:
            tournament_id = import_tournament_results(
                connection=self._connection,
                file_path=file_path,
                tournament_name=tournament_name,
                tournament_date=tournament_date,
                category_code=category_code,
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Импорт", str(exc))
            return

        if self._tournaments_view is not None:
            refresh = getattr(self._tournaments_view, "refresh_latest_tournament", None)
            if callable(refresh):
                refresh(tournament_id)

        QMessageBox.information(self, "Импорт", "Импорт завершён.")

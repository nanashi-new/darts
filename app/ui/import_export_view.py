from PySide6.QtWidgets import (
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)

from app.services.import_xlsx import parse_first_table_from_xlsx, validate_rows
from app.ui.import_preview_dialog import ImportPreviewDialog


class ImportExportView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Демо-импорт Excel: выберите файл для предпросмотра."))

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

        headers, rows = parse_first_table_from_xlsx(file_path)
        if not rows:
            QMessageBox.information(
                self,
                "Импорт",
                "Не удалось найти таблицу в файле.",
            )
            return

        warnings = validate_rows(rows)
        dialog = ImportPreviewDialog(rows, warnings, self)
        dialog.exec()

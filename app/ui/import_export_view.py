from dataclasses import replace

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QDateEdit,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.db.database import get_connection
from app.services.import_xlsx import (
    TableBlock,
    import_batch_from_folder,
    import_tournament_results,
    import_tournament_rows,
    read_table_block_preview,
    parse_table_block_with_mapping,
    list_import_profiles,
    parse_tables_from_xlsx_with_report,
    save_import_profile,
    delete_import_profile,
)
from app.ui.column_mapping_dialog import ColumnMappingDialog
from app.ui.import_preview_dialog import ImportPreviewDialog
from app.ui.player_match_dialog import PlayerMatchDialog


class TableBlocksDialog(QDialog):
    def __init__(self, blocks: list[TableBlock], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Найденные таблицы")
        self.resize(700, 420)
        self._blocks = blocks

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Выберите блоки для импорта:", self))

        self.list_widget = QListWidget(self)
        for block in blocks:
            text = f"{block.sheet_name}: строки {block.start_row}-{block.end_row} (записей: {len(block.rows)})"
            item = QListWidgetItem(text)
            item.setFlags(item.flags() | item.flags().ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)

        preview_button = QPushButton("Предпросмотр выбранного блока", self)
        preview_button.clicked.connect(self._preview_selected)
        layout.addWidget(preview_button)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def selected_indexes(self) -> list[int]:
        selected: list[int] = []
        for idx in range(self.list_widget.count()):
            item = self.list_widget.item(idx)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(idx)
        return selected

    def _preview_selected(self) -> None:
        row = self.list_widget.currentRow()
        if row < 0:
            QMessageBox.information(self, "Предпросмотр", "Выберите блок в списке.")
            return
        block = self._blocks[row]
        dialog = ImportPreviewDialog(block.rows, block.warnings, self)
        dialog.exec()


class ImportProfilesDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Профили импорта")
        self.resize(500, 360)

        layout = QVBoxLayout(self)
        self.list_widget = QListWidget(self)
        layout.addWidget(self.list_widget)

        controls = QHBoxLayout()
        add_button = QPushButton("Добавить", self)
        add_button.clicked.connect(self._add_profile)
        remove_button = QPushButton("Удалить", self)
        remove_button.clicked.connect(self._remove_profile)
        controls.addWidget(add_button)
        controls.addWidget(remove_button)
        layout.addLayout(controls)

        close_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        close_box.rejected.connect(self.reject)
        close_box.accepted.connect(self.accept)
        layout.addWidget(close_box)

        self._profiles = []
        self._reload()

    def _reload(self) -> None:
        self._profiles = list_import_profiles()
        self.list_widget.clear()
        for profile in self._profiles:
            self.list_widget.addItem(f"{profile.name} ({', '.join(profile.required_columns)})")

    def _add_profile(self) -> None:
        name, ok = QInputDialog.getText(self, "Имя профиля", "Название:")
        if not ok or not name.strip():
            return
        required, ok = QInputDialog.getText(
            self,
            "Обязательные колонки",
            "Внутренние ключи через запятую (например: fio,place,score_set):",
        )
        if not ok:
            return
        save_import_profile(
            {
                "name": name.strip(),
                "required_columns": [item.strip() for item in required.split(",") if item.strip()],
                "header_aliases": {},
            }
        )
        self._reload()

    def _remove_profile(self) -> None:
        row = self.list_widget.currentRow()
        if row < 0:
            return
        profile = self._profiles[row]
        delete_import_profile(profile.name)
        self._reload()


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

        self.import_folder_button = QPushButton("Импорт папки")
        self.import_folder_button.clicked.connect(self._on_import_folder_clicked)
        layout.addWidget(self.import_folder_button)

        self.import_profiles_button = QPushButton("Профили импорта")
        self.import_profiles_button.clicked.connect(self._on_import_profiles_clicked)
        layout.addWidget(self.import_profiles_button)


    def _resolve_player_match(
        self,
        fio: str,
        birth_date_or_year: str | None,
        candidates: list[dict[str, object]],
    ) -> dict[str, object] | None:
        dialog = PlayerMatchDialog(
            fio=fio,
            birth_date_or_year=birth_date_or_year,
            candidates=candidates,
            parent=self,
        )
        dialog.exec()
        return dialog.resolution()

    def _on_import_clicked(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите XLSX", "", "Excel файлы (*.xlsx)")
        if not file_path:
            return

        blocks = parse_tables_from_xlsx_with_report(file_path)
        if not blocks:
            QMessageBox.information(self, "Импорт", "Не удалось найти таблицы в файле.")
            return

        blocks_dialog = TableBlocksDialog(blocks, self)
        if blocks_dialog.exec() != QDialog.DialogCode.Accepted:
            return
        selected = blocks_dialog.selected_indexes()
        if not selected:
            QMessageBox.information(self, "Импорт", "Не выбраны блоки для импорта.")
            return

        preview_block = blocks[selected[0]]
        if preview_block.needs_mapping or preview_block.confidence < 1.0:
            headers, preview_rows = read_table_block_preview(file_path, preview_block)
            mapping_dialog = ColumnMappingDialog(headers, preview_rows, self)
            if mapping_dialog.exec() != QDialog.DialogCode.Accepted:
                return

            selected_mapping = mapping_dialog.mapping()
            header_aliases = {
                key: [header]
                for key, header in selected_mapping.items()
                if header
            }
            save_import_profile(
                {
                    "name": f"wizard:{preview_block.sheet_name}:{preview_block.start_row}",
                    "required_columns": ["fio", "place", "score_set"],
                    "header_aliases": header_aliases,
                }
            )

            mapped_rows = parse_table_block_with_mapping(file_path, preview_block, selected_mapping)
            preview_block = replace(
                preview_block,
                rows=mapped_rows,
                needs_mapping=False,
                confidence=1.0,
                missing_required_columns=[],
                errors=[],
            )

        preview = ImportPreviewDialog(preview_block.rows, preview_block.warnings, self)
        if preview.exec() != QDialog.DialogCode.Accepted:
            return

        tournament_name = self.tournament_name_input.text().strip()
        if not tournament_name:
            QMessageBox.warning(self, "Импорт", "Введите название турнира.")
            return

        tournament_date = self.tournament_date_input.date().toString("yyyy-MM-dd")
        category_code = self.category_code_input.text().strip() or None

        try:
            if preview_block.rows:
                tournament_id, norms_loaded = import_tournament_rows(
                    connection=self._connection,
                    rows=preview_block.rows,
                    tournament_name=tournament_name,
                    tournament_date=tournament_date,
                    category_code=category_code,
                    source_files=[file_path],
                    player_match_resolver=self._resolve_player_match,
                )
            else:
                tournament_id, norms_loaded = import_tournament_results(
                    connection=self._connection,
                    file_path=file_path,
                    tournament_name=tournament_name,
                    tournament_date=tournament_date,
                    category_code=category_code,
                    player_match_resolver=self._resolve_player_match,
                )
        except ValueError as exc:
            QMessageBox.warning(self, "Импорт", str(exc))
            return

        if self._tournaments_view is not None:
            refresh = getattr(self._tournaments_view, "refresh_latest_tournament", None)
            if callable(refresh):
                refresh(tournament_id)

        if not norms_loaded:
            QMessageBox.warning(self, "Импорт", "Нормативы не загружены.")
        QMessageBox.information(self, "Импорт", "Импорт завершён.")

    def _on_import_folder_clicked(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку с XLSX")
        if not folder:
            return
        result = import_batch_from_folder(folder)
        QMessageBox.information(
            self,
            "Импорт папки",
            f"Успешно: {result['success']}\nОшибок: {result['error']}",
        )

    def _on_import_profiles_clicked(self) -> None:
        dialog = ImportProfilesDialog(self)
        dialog.exec()

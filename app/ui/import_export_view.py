from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.db.database import get_connection
from app.db.repositories import TournamentRepository
from app.domain.tournament_lifecycle import TournamentStatus
from app.services.audit_log import AuditLogService, ERROR, IMPORT_FILE, IMPORT_FOLDER
from app.services.category_suggestion import suggest_category_code
from app.services.import_report import build_import_session_report, persist_import_session_report
from app.services.import_review import build_import_rating_preview
from app.services.league_transfer import build_league_transfer_preview
from app.services.import_pipeline import (
    parse_tables_from_clipboard_text,
    parse_tables_from_file,
)
from app.services.import_xlsx import (
    ImportApplyReport,
    TableBlock,
    delete_import_profile,
    import_batch_from_folder,
    import_tournament_table_blocks,
    list_import_profiles,
    parse_table_block_with_mapping,
    parse_tables_from_xlsx_with_report,
    read_table_block_preview,
    save_import_profile,
)
from app.services.tournament_lifecycle import transition_tournament_status
from app.ui.column_mapping_dialog import ColumnMappingDialog
from app.ui.import_apply_review_dialog import ImportApplyReviewDialog
from app.ui.import_preview_dialog import ImportPreviewDialog
from app.ui.labels import category_label, tournament_status_label
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
        if ok_button := button_box.button(QDialogButtonBox.StandardButton.Ok):
            ok_button.setText("Импортировать выбранные")
        if cancel_button := button_box.button(QDialogButtonBox.StandardButton.Cancel):
            cancel_button.setText("Отмена")
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
        if close_button := close_box.button(QDialogButtonBox.StandardButton.Close):
            close_button.setText("Закрыть")
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
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._connection = get_connection()
        self._tournament_repo = TournamentRepository(self._connection)
        self._audit_log_service = AuditLogService(self._connection)
        self._tournaments_view = tournaments_view
        self.setAcceptDrops(True)

        root_layout = QVBoxLayout(self)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        root_layout.addWidget(scroll_area)

        content = QWidget(self)
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        scroll_area.setWidget(content)

        layout = QVBoxLayout(content)
        layout.addWidget(QLabel("Импорт Excel: выберите файл для предпросмотра."))

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

        self.category_hint_label = QLabel("", self)
        self.category_hint_label.setWordWrap(True)
        form_layout.addRow("", self.category_hint_label)

        self.is_adult_mode_checkbox = QCheckBox("Взрослый режим", self)
        form_layout.addRow("Режим:", self.is_adult_mode_checkbox)
        layout.addLayout(form_layout)

        self.import_button = QPushButton("Импорт файла", self)
        self.import_button.setToolTip("Выбрать XLSX-файл и пройти предпросмотр перед импортом.")
        self.import_button.clicked.connect(self._on_import_clicked)
        layout.addWidget(self.import_button)

        self.import_folder_button = QPushButton("Импорт папки", self)
        self.import_folder_button.clicked.connect(self._on_import_folder_clicked)
        layout.addWidget(self.import_folder_button)

        self.import_profiles_button = QPushButton("Профили импорта", self)
        self.import_profiles_button.clicked.connect(self._on_import_profiles_clicked)
        layout.addWidget(self.import_profiles_button)

        self.import_csv_json_button = QPushButton("Импорт CSV/JSON", self)
        self.import_csv_json_button.setToolTip("Выбрать CSV или JSON файл для импорта.")
        self.import_csv_json_button.clicked.connect(self._on_import_csv_json_clicked)
        layout.addWidget(self.import_csv_json_button)

        self.paste_clipboard_button = QPushButton("Вставить из буфера (Ctrl+V)", self)
        self.paste_clipboard_button.setToolTip("Вставить данные из буфера обмена (Excel/Google Sheets).")
        self.paste_clipboard_button.clicked.connect(self._on_paste_clipboard_clicked)
        layout.addWidget(self.paste_clipboard_button)

        layout.addStretch(1)

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

    def _persist_import_session_report(self, apply_report: ImportApplyReport, *, apply_status: str) -> None:
        report = build_import_session_report(
            connection=self._connection,
            apply_report=apply_report,
            apply_status=apply_status,
        )
        persist_import_session_report(connection=self._connection, report=report)

    def _on_import_clicked(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите XLSX", "", "Excel файлы (*.xlsx)")
        if not file_path:
            return

        blocks = parse_tables_from_xlsx_with_report(file_path)
        if not blocks:
            self._audit_log_service.log_event(
                IMPORT_FILE,
                "Импорт файла: таблицы не найдены",
                f"Файл: {file_path}",
                level="warning",
                context={"path": file_path},
            )
            QMessageBox.information(self, "Импорт", "Не удалось найти таблицы в файле.")
            return

        blocks_dialog = TableBlocksDialog(blocks, self)
        if blocks_dialog.exec() != QDialog.DialogCode.Accepted:
            return
        selected = blocks_dialog.selected_indexes()
        if not selected:
            QMessageBox.information(self, "Импорт", "Не выбраны блоки для импорта.")
            return

        selected_blocks: list[TableBlock] = []
        for block_index in selected:
            block = blocks[block_index]
            if block.needs_mapping or block.confidence < 1.0:
                headers, preview_rows = read_table_block_preview(file_path, block)
                mapping_dialog = ColumnMappingDialog(headers, preview_rows, self)
                if mapping_dialog.exec() != QDialog.DialogCode.Accepted:
                    return

                selected_mapping = mapping_dialog.mapping()
                header_aliases = {key: [header] for key, header in selected_mapping.items() if header}
                save_import_profile(
                    {
                        "name": f"wizard:{block.sheet_name}:{block.start_row}",
                        "required_columns": [
                            key
                            for key in (
                                "fio",
                                "birth_year" if selected_mapping.get("birth_year") else "birth_date",
                                "place",
                                "score_set",
                                "score_sector20",
                                "score_big_round",
                            )
                            if selected_mapping.get(key)
                        ],
                        "header_aliases": header_aliases,
                    }
                )

                mapped_rows = parse_table_block_with_mapping(file_path, block, selected_mapping)
                block = replace(
                    block,
                    rows=mapped_rows,
                    needs_mapping=False,
                    confidence=1.0,
                    missing_required_columns=[],
                    errors=[],
                )
            selected_blocks.append(block)

        preview_rows = [row for block in selected_blocks for row in block.rows]
        preview_warnings = [
            f"{block.sheet_name}:{block.start_row} - {warning}"
            for block in selected_blocks
            for warning in block.warnings
        ]
        self._update_category_hint(preview_rows)

        preview = ImportPreviewDialog(preview_rows, preview_warnings, self)
        if preview.exec() != QDialog.DialogCode.Accepted:
            return

        tournament_name = self.tournament_name_input.text().strip()
        if not tournament_name:
            QMessageBox.warning(self, "Импорт", "Введите название турнира.")
            return

        tournament_date = self.tournament_date_input.date().toString("yyyy-MM-dd")
        category_code = self.category_code_input.text().strip() or None
        is_adult_mode = self.is_adult_mode_checkbox.isChecked()
        operation_group_id = uuid4().hex

        try:
            apply_report = import_tournament_table_blocks(
                connection=self._connection,
                blocks=selected_blocks,
                tournament_name=tournament_name,
                tournament_date=tournament_date,
                category_code=category_code,
                is_adult_mode=is_adult_mode,
                source_files=[file_path],
                player_match_resolver=self._resolve_player_match,
                operation_group_id=operation_group_id,
            )
        except ValueError as exc:
            self._audit_log_service.log_event(
                ERROR,
                "Ошибка импорта файла",
                str(exc),
                level="error",
                context={"path": file_path},
                operation_group_id=operation_group_id,
            )
            QMessageBox.warning(self, "Импорт", str(exc))
            return

        tournament_id = apply_report.tournament_id
        if self._tournaments_view is not None:
            refresh = getattr(self._tournaments_view, "refresh_latest_tournament", None)
            if callable(refresh):
                refresh(tournament_id)

        self._audit_log_service.log_event(
            IMPORT_FILE,
            "Импорт файла: применено в черновик",
            (
                f"Турнир ID: {tournament_id}; импортировано: {apply_report.imported_rows}; "
                f"пропущено: {apply_report.skipped_rows}; предупреждений: {len(apply_report.warnings)}"
            ),
            context={"path": file_path, "tournament_id": tournament_id},
            operation_group_id=apply_report.operation_group_id or None,
        )
        self._show_apply_review(apply_report)

    def _show_apply_review(self, apply_report: ImportApplyReport) -> None:
        rating_preview = build_import_rating_preview(
            connection=self._connection,
            tournament_id=apply_report.tournament_id,
            n_value=3,
        )
        league_preview = build_league_transfer_preview(
            connection=self._connection,
            tournament_id=apply_report.tournament_id,
        )
        dialog = ImportApplyReviewDialog(
            apply_report=apply_report,
            rating_preview=rating_preview,
            league_preview=league_preview,
            parent=self,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._publish_imported_tournament(apply_report)
            return

        self._persist_import_session_report(apply_report, apply_status="draft_applied")
        self._audit_log_service.log_event(
            IMPORT_FILE,
            "Импорт файла завершен без публикации",
            f"Турнир ID: {apply_report.tournament_id} оставлен в статусе черновика",
            level="warning",
            context={"tournament_id": apply_report.tournament_id, "status": apply_report.tournament_status},
            operation_group_id=apply_report.operation_group_id or None,
        )
        QMessageBox.information(self, "Импорт", "Импорт завершен. Турнир оставлен в статусе черновика.")

    def _update_category_hint(self, rows: list[dict[str, object]]) -> None:
        self.category_hint_label.clear()
        if self.is_adult_mode_checkbox.isChecked() or self.category_code_input.text().strip():
            return
        tournament_date = self.tournament_date_input.date().toString("yyyy-MM-dd")
        for row in rows:
            suggested = suggest_category_code(
                birth_date_or_year=row.get("birth"),
                tournament_date=tournament_date,
            )
            if not suggested:
                continue
            self.category_code_input.setPlaceholderText(f"Подсказка: {suggested}")
            self.category_code_input.setToolTip(
                "Подсказка рассчитана по дате рождения первой подходящей строки. "
                "Проверьте категорию и введите код, если она подходит."
            )
            self.category_hint_label.setText(
                f"Подсказка категории: {suggested} - {category_label(suggested)}. "
                "Введите код вручную, если это верно."
            )
            return

    def _publish_imported_tournament(self, apply_report: ImportApplyReport) -> None:
        transitions = (
            TournamentStatus.REVIEW.value,
            TournamentStatus.CONFIRMED.value,
            TournamentStatus.PUBLISHED.value,
        )
        for target_status in transitions:
            transition_result = transition_tournament_status(
                connection=self._connection,
                tournament_id=apply_report.tournament_id,
                to_status=target_status,
                context={
                    "actor": "import_wizard",
                    "operation_group_id": apply_report.operation_group_id,
                },
            )
            if not transition_result.get("ok"):
                error_payload = transition_result.get("error") or {}
                message = str(error_payload.get("message") or "Не удалось изменить статус турнира.")
                details = error_payload.get("details")
                self._audit_log_service.log_event(
                    ERROR,
                    "Ошибка публикации после импорта",
                    f"{message}; детали={details}",
                    level="error",
                    context={"tournament_id": apply_report.tournament_id, "target_status": target_status},
                    operation_group_id=apply_report.operation_group_id or None,
                )
                QMessageBox.warning(
                    self,
                    "Публикация",
                    f"Не удалось перейти в статус «{tournament_status_label(target_status)}».\n{message}",
                )
                return

        self._persist_import_session_report(apply_report, apply_status="published")

        if self._tournaments_view is not None:
            refresh = getattr(self._tournaments_view, "refresh_latest_tournament", None)
            if callable(refresh):
                refresh(apply_report.tournament_id)

        tournament = self._tournament_repo.get(apply_report.tournament_id)
        published_status = (
            str(tournament.get("status"))
            if tournament is not None
            else TournamentStatus.PUBLISHED.value
        )
        self._audit_log_service.log_event(
            IMPORT_FILE,
            "Импорт файла завершен, публикация подтверждена",
            (
                f"Турнир ID: {apply_report.tournament_id}; "
                f"статус={tournament_status_label(published_status)}; "
                f"импортировано={apply_report.imported_rows}; предупреждений={len(apply_report.warnings)}"
            ),
            context={"tournament_id": apply_report.tournament_id, "status": published_status},
            operation_group_id=apply_report.operation_group_id or None,
        )
        QMessageBox.information(
            self,
            "Импорт",
            f"Импорт завершён и турнир опубликован.\nТурнир ID: {apply_report.tournament_id}",
        )

    def _on_import_csv_json_clicked(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите CSV или JSON", "", "CSV/JSON файлы (*.csv *.json);;CSV (*.csv);;JSON (*.json)"
        )
        if not file_path:
            return

        blocks = parse_tables_from_file(file_path)
        if not blocks:
            self._audit_log_service.log_event(
                IMPORT_FILE,
                "Импорт файла: таблицы не найдены",
                f"Файл: {file_path}",
                level="warning",
                context={"path": file_path},
            )
            QMessageBox.information(self, "Импорт", "Не удалось найти таблицы в файле.")
            return

        self._import_blocks(blocks, source_files=[file_path])

    def _on_paste_clipboard_clicked(self) -> None:
        clipboard = QApplication.clipboard()
        if clipboard is None:
            QMessageBox.information(self, "Импорт", "Буфер обмена недоступен.")
            return
        text = clipboard.text()
        if not text or not text.strip():
            QMessageBox.information(self, "Импорт", "Буфер обмена пуст.")
            return

        blocks = parse_tables_from_clipboard_text(text)
        if not blocks:
            QMessageBox.information(self, "Импорт", "Не удалось распознать таблицу из буфера обмена.")
            return

        self._import_blocks(blocks, source_files=["clipboard"])

    def _import_blocks(self, blocks: list[TableBlock], *, source_files: list[str]) -> None:
        blocks_dialog = TableBlocksDialog(blocks, self)
        if blocks_dialog.exec() != QDialog.DialogCode.Accepted:
            return
        selected = blocks_dialog.selected_indexes()
        if not selected:
            QMessageBox.information(self, "Импорт", "Не выбраны блоки для импорта.")
            return

        selected_blocks: list[TableBlock] = [blocks[i] for i in selected]

        preview_rows = [row for block in selected_blocks for row in block.rows]
        preview_warnings = [
            f"{block.sheet_name}:{block.start_row} - {warning}"
            for block in selected_blocks
            for warning in block.warnings
        ]
        self._update_category_hint(preview_rows)

        preview = ImportPreviewDialog(preview_rows, preview_warnings, self)
        if preview.exec() != QDialog.DialogCode.Accepted:
            return

        tournament_name = self.tournament_name_input.text().strip()
        if not tournament_name:
            QMessageBox.warning(self, "Импорт", "Введите название турнира.")
            return

        tournament_date = self.tournament_date_input.date().toString("yyyy-MM-dd")
        category_code = self.category_code_input.text().strip() or None
        is_adult_mode = self.is_adult_mode_checkbox.isChecked()
        operation_group_id = uuid4().hex

        try:
            apply_report = import_tournament_table_blocks(
                connection=self._connection,
                blocks=selected_blocks,
                tournament_name=tournament_name,
                tournament_date=tournament_date,
                category_code=category_code,
                is_adult_mode=is_adult_mode,
                source_files=source_files,
                player_match_resolver=self._resolve_player_match,
                operation_group_id=operation_group_id,
            )
        except ValueError as exc:
            self._audit_log_service.log_event(
                ERROR,
                "Ошибка импорта файла",
                str(exc),
                level="error",
                context={"source": str(source_files)},
                operation_group_id=operation_group_id,
            )
            QMessageBox.warning(self, "Импорт", str(exc))
            return

        tournament_id = apply_report.tournament_id
        if self._tournaments_view is not None:
            refresh = getattr(self._tournaments_view, "refresh_latest_tournament", None)
            if callable(refresh):
                refresh(tournament_id)

        self._audit_log_service.log_event(
            IMPORT_FILE,
            "Импорт файла: применено в черновик",
            (
                f"Турнир ID: {tournament_id}; импортировано: {apply_report.imported_rows}; "
                f"пропущено: {apply_report.skipped_rows}; предупреждений: {len(apply_report.warnings)}"
            ),
            context={"source": str(source_files), "tournament_id": tournament_id},
            operation_group_id=apply_report.operation_group_id or None,
        )
        self._show_apply_review(apply_report)

    def _on_import_folder_clicked(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку с XLSX")
        if not folder:
            return
        result = import_batch_from_folder(folder)
        level = "warning" if result["error"] else "info"
        self._audit_log_service.log_event(
            IMPORT_FOLDER,
            "Импорт папки завершён",
            f"Успешно: {result['success']}; ошибок: {result['error']}",
            level=level,
            context={"folder": folder, "success": result["success"], "error": result["error"]},
        )
        QMessageBox.information(
            self,
            "Импорт папки",
            f"Успешно: {result['success']}\nОшибок: {result['error']}",
        )

    def _on_import_profiles_clicked(self) -> None:
        dialog = ImportProfilesDialog(self)
        dialog.exec()

    def dragEnterEvent(self, event: object) -> None:  # type: ignore[override]
        from PySide6.QtGui import QDragEnterEvent

        if not isinstance(event, QDragEnterEvent):
            return
        mime = event.mimeData()
        if mime is not None and mime.hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: object) -> None:  # type: ignore[override]
        from PySide6.QtGui import QDropEvent

        if not isinstance(event, QDropEvent):
            return
        mime = event.mimeData()
        if mime is None or not mime.hasUrls():
            return
        paths: list[str] = []
        for url in mime.urls():
            local = url.toLocalFile()
            if local:
                paths.append(local)
        if paths:
            self.handle_dropped_files(paths)
        event.acceptProposedAction()

    def handle_dropped_files(self, paths: list[str]) -> None:
        """Process files dropped onto the import view."""
        all_blocks: list[TableBlock] = []
        for path in paths:
            blocks = parse_tables_from_file(path)
            all_blocks.extend(blocks)

        if not all_blocks:
            QMessageBox.information(self, "Импорт", "Не удалось найти таблицы в перетащенных файлах.")
            return

        self._import_blocks(all_blocks, source_files=paths)

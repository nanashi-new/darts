from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from app.db.database import get_connection
from app.db.repositories import ResultRepository, TournamentRepository
from app.domain.tournament_lifecycle import TournamentStatus, allowed_targets
from app.services.audit_log import AuditLogService, ERROR, EXPORT_FILE, RECALC_TOURNAMENT
from app.services.export_service import ExportService
from app.services.league_transfer import build_league_transfer_preview
from app.services.manual_tournament import create_manual_adult_tournament
from app.services.notes import EntityNoteDefaults
from app.services.recalculate_tournament import recalculate_tournament_results
from app.services.tournament_correction import (
    TournamentCorrectionError,
    correct_tournament,
)
from app.services.tournament_lifecycle import transition_tournament_status
from app.ui.entity_notes_dialog import EntityNotesDialog
from app.ui.labels import category_label as display_category_label
from app.ui.labels import tournament_status_label
from app.ui.manual_tournament_dialog import ManualTournamentDialog
from app.ui.messages import confirm_yes_no


class TournamentsView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._connection = get_connection()
        self._tournament_repo = TournamentRepository(self._connection)
        self._result_repo = ResultRepository(self._connection)
        self._export_service = ExportService()
        self._audit_log_service = AuditLogService(self._connection)
        self._current_tournament: dict[str, object] | None = None

        layout = QVBoxLayout(self)
        self.header_label = QLabel("Турниры пока не загружены.", self)
        layout.addWidget(self.header_label)
        self.status_label = QLabel("Статус: —", self)
        layout.addWidget(self.status_label)
        self.metadata_label = QLabel("Метаданные: —", self)
        self.metadata_label.setWordWrap(True)
        layout.addWidget(self.metadata_label)

        self.results_table = QTableView(self)
        self.results_table.setSortingEnabled(False)
        layout.addWidget(self.results_table)
        layout.addLayout(self._build_actions())

        self.refresh_latest_tournament()

    def _build_actions(self) -> QHBoxLayout:
        actions_layout = QHBoxLayout()
        self._create_adult_btn = QPushButton("Взрослый черновик", self)
        self._notes_btn = QPushButton("Заметки", self)
        self._recalc_btn = QPushButton("Пересчитать турнир", self)
        self._submit_review_btn = QPushButton("Отправить на проверку", self)
        self._confirm_btn = QPushButton("Подтвердить", self)
        self._publish_btn = QPushButton("Опубликовать", self)
        self._archive_btn = QPushButton("Архивировать", self)
        self._correction_btn = QPushButton("Коррекция", self)
        self._format_combo = QComboBox(self)
        self._format_combo.addItems(["PDF", "XLSX", "PNG"])
        self._image_mode_combo = QComboBox(self)
        self._image_mode_combo.addItems(["Сохранить видимую область", "Сохранить всю таблицу"])
        self._export_btn = QPushButton("Экспорт", self)
        self._print_btn = QPushButton("Печать", self)
        self._lifecycle_hint_label = QLabel("", self)
        self._lifecycle_hint_label.setWordWrap(True)

        self._create_adult_btn.clicked.connect(self._create_manual_adult_tournament)
        self._notes_btn.clicked.connect(self._open_tournament_notes)
        self._recalc_btn.clicked.connect(self._recalculate_tournament)
        self._submit_review_btn.clicked.connect(
            lambda: self._transition_tournament(TournamentStatus.REVIEW.value, "Отправка на проверку")
        )
        self._confirm_btn.clicked.connect(
            lambda: self._transition_tournament(TournamentStatus.CONFIRMED.value, "Подтверждение")
        )
        self._publish_btn.clicked.connect(
            lambda: self._transition_tournament(TournamentStatus.PUBLISHED.value, "Публикация")
        )
        self._archive_btn.clicked.connect(
            lambda: self._transition_tournament(TournamentStatus.ARCHIVED.value, "Архивация")
        )
        self._correction_btn.clicked.connect(self._start_correction)
        self._export_btn.clicked.connect(self._export_selected_format)
        self._print_btn.clicked.connect(self._print_table)

        actions_layout.addWidget(self._create_adult_btn)
        actions_layout.addWidget(self._notes_btn)
        actions_layout.addWidget(self._recalc_btn)
        actions_layout.addWidget(self._submit_review_btn)
        actions_layout.addWidget(self._confirm_btn)
        actions_layout.addWidget(self._publish_btn)
        actions_layout.addWidget(self._archive_btn)
        actions_layout.addWidget(self._correction_btn)
        actions_layout.addWidget(QLabel("Формат:"))
        actions_layout.addWidget(self._format_combo)
        actions_layout.addWidget(self._image_mode_combo)
        actions_layout.addWidget(self._export_btn)
        actions_layout.addWidget(self._print_btn)
        actions_layout.addWidget(self._lifecycle_hint_label)

        actions_layout.addStretch(1)
        return actions_layout

    def refresh_latest_tournament(self, tournament_id: int | None = None) -> None:
        tournament = (
            self._tournament_repo.get(tournament_id)
            if tournament_id is not None
            else self._tournament_repo.get_latest()
        )
        if not tournament:
            self._current_tournament = None
            self.header_label.setText("Турниры пока не загружены.")
            self.status_label.setText("Статус: —")
            self.metadata_label.setText("Метаданные: —")
            self.results_table.setModel(QStandardItemModel(self))
            self._notes_btn.setEnabled(False)
            self._refresh_lifecycle_controls()
            return

        self._current_tournament = tournament
        date_label = tournament.get("date") or "дата не указана"
        category_label = (
            display_category_label(tournament.get("category_code"))
            if tournament.get("category_code")
            else "категория не указана"
        )
        status_label = tournament_status_label(tournament.get("status") or TournamentStatus.DRAFT.value)
        self.header_label.setText(
            f"Турнир: {tournament.get('name')} — {date_label} ({category_label})"
        )
        self.status_label.setText(f"Статус: {status_label}")
        self.metadata_label.setText(f"Метаданные: {self._format_metadata(tournament)}")

        results = self._result_repo.list_with_players(int(tournament["id"]))
        self._set_results_table(results)
        self._notes_btn.setEnabled(True)
        self._refresh_lifecycle_controls()

    def _set_results_table(self, results: list[dict[str, object]]) -> None:
        header_order = [
            ("place", "Место"),
            ("fio", "ФИО"),
            ("birth_date", "Дата рождения"),
            ("score_set", "Набор очков"),
            ("score_sector20", "Сектор 20"),
            ("score_big_round", "Большой раунд"),
            ("points_place", "Очки за место"),
            ("points_classification", "Очки классификации"),
            ("points_total", "Итого"),
        ]
        model = QStandardItemModel(self)
        model.setColumnCount(len(header_order))
        model.setHorizontalHeaderLabels([label for _, label in header_order])

        for result in results:
            last_name = result.get("last_name") or ""
            first_name = result.get("first_name") or ""
            middle_name = result.get("middle_name") or ""
            fio = " ".join(part for part in [last_name, first_name, middle_name] if part)
            row_items = []
            row_data = {
                **result,
                "fio": fio,
            }
            for key, _ in header_order:
                value = row_data.get(key)
                display = "" if value is None else str(value)
                row_items.append(QStandardItem(display))
            model.appendRow(row_items)

        self.results_table.setModel(model)
        self.results_table.resizeColumnsToContents()

    def _export_selected_format(self) -> None:
        if not self._current_tournament:
            QMessageBox.warning(self, "Экспорт протокола", "Турнир не выбран.")
            return
        selected_format = self._format_combo.currentText().lower()
        defaults = {
            "pdf": "tournament_protocol.pdf",
            "xlsx": "tournament_protocol.xlsx",
            "png": "tournament_protocol.png",
        }
        filters = {
            "pdf": "Файлы PDF (*.pdf)",
            "xlsx": "Файлы Excel (*.xlsx)",
            "png": "Изображения (*.png *.jpg)",
        }
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт протокола",
            defaults[selected_format],
            filters[selected_format],
        )
        if not path:
            QMessageBox.warning(self, "Экспорт протокола", "Путь для сохранения не выбран.")
            return

        if selected_format == "png" and not path.lower().endswith((".png", ".jpg", ".jpeg")):
            chosen_extension, accepted = QInputDialog.getItem(
                self,
                "Формат изображения",
                "Расширение:",
                ["png", "jpg"],
                editable=False,
            )
            if not accepted:
                return
            path = f"{path}.{chosen_extension}"

        try:
            if selected_format in {"pdf", "xlsx"}:
                self._export_service.export_dataset(
                    export_format=selected_format,
                    path=path,
                    header_lines=self._build_export_header(),
                    columns=[
                        "Место",
                        "ФИО",
                        "Дата рождения",
                        "Набор очков",
                        "Сектор 20",
                        "Большой раунд",
                        "Очки за место",
                        "Очки классификации",
                        "Итого",
                    ],
                    rows=self._table_rows(),
                )
            else:
                full_table = self._image_mode_combo.currentIndex() == 1
                self._export_service.save_table_image(self.results_table, path, full_table=full_table)
        except (OSError, ValueError) as exc:
            self._audit_log_service.log_event(
                ERROR,
                "Ошибка экспорта протокола",
                str(exc),
                level="error",
                context={"path": path, "format": selected_format},
            )
            QMessageBox.critical(self, "Экспорт протокола", str(exc))
            return
        self._audit_log_service.log_event(
            EXPORT_FILE,
            "Экспорт протокола",
            f"Формат: {selected_format}; путь: {path}",
            context={"path": path, "format": selected_format},
        )
        QMessageBox.information(self, "Экспорт протокола", f"Готово: {path}")

    def _print_table(self) -> None:
        if not self._current_tournament:
            QMessageBox.warning(self, "Печать", "Турнир не выбран.")
            return
        if self._export_service.print_table(
            self.results_table, self, self._build_export_header()
        ):
            QMessageBox.information(self, "Печать", "Печать отправлена на принтер.")

    def _recalculate_tournament(self) -> None:
        if not self._current_tournament:
            QMessageBox.warning(self, "Пересчет", "Турнир не выбран.")
            return
        tournament_id = int(self._current_tournament["id"])
        try:
            report = recalculate_tournament_results(
                connection=self._connection,
                tournament_id=tournament_id,
            )
        except ValueError as exc:
            self._audit_log_service.log_event(
                ERROR,
                "Ошибка пересчёта турнира",
                str(exc),
                level="error",
                context={"tournament_id": tournament_id},
            )
            QMessageBox.warning(self, "Пересчет", str(exc))
            return
        self.refresh_latest_tournament(tournament_id)
        self._audit_log_service.log_event(
            RECALC_TOURNAMENT,
            "Пересчёт турнира",
            (
                f"Турнир ID: {tournament_id}; обновлено: {report.results_updated}; "
                f"предупреждений: {len(report.warnings)}; ошибок: {len(report.errors)}"
            ),
            level="error" if report.errors else "warning" if report.warnings else "info",
            context={"tournament_id": tournament_id},
        )
        details = [
            f"Обновлено результатов: {report.results_updated}",
            f"Предупреждений: {len(report.warnings)}",
            f"Ошибок: {len(report.errors)}",
        ]
        if report.warnings:
            details.append("\n".join(report.warnings[:3]))
        if report.errors:
            details.append("\n".join(report.errors[:3]))
        QMessageBox.information(self, "Пересчет", "\n".join(details))

    def _table_rows(self) -> list[list[str]]:
        model = self.results_table.model()
        if model is None:
            return []
        rows: list[list[str]] = []
        for row in range(model.rowCount()):
            rows.append([str(model.index(row, column).data() or "") for column in range(model.columnCount())])
        return rows

    def _format_metadata(self, tournament: dict[str, object]) -> str:
        keys = [
            ("league_code", "Лига"),
            ("type", "Тип"),
            ("season", "Сезон"),
            ("series", "Серия"),
            ("location", "Локация"),
            ("organizer", "Организатор"),
            ("has_draft_changes", "Черновые изменения"),
            ("warning_state", "Состояние предупреждений"),
            ("error_state", "Состояние ошибок"),
            ("confirmed_by", "Подтвердил"),
            ("published_by", "Опубликовал"),
        ]
        chunks: list[str] = []
        for key, label in keys:
            raw_value = tournament.get(key)
            if raw_value in (None, ""):
                continue
            if key == "has_draft_changes":
                value = "да" if bool(raw_value) else "нет"
            elif key in {"warning_state", "error_state"} and str(raw_value) == "none":
                value = "нет"
            elif key == "type" and str(raw_value) == "standard":
                value = "обычный"
            else:
                value = str(raw_value)
            chunks.append(f"{label}: {value}")
        return "; ".join(chunks) if chunks else "нет ключевых метаданных"

    def _refresh_lifecycle_controls(self) -> None:
        action_buttons = [
            (self._submit_review_btn, TournamentStatus.REVIEW.value),
            (self._confirm_btn, TournamentStatus.CONFIRMED.value),
            (self._publish_btn, TournamentStatus.PUBLISHED.value),
            (self._archive_btn, TournamentStatus.ARCHIVED.value),
        ]
        if not self._current_tournament:
            for button, _ in action_buttons:
                button.setEnabled(False)
                button.setToolTip("Турнир не выбран.")
            self._correction_btn.setEnabled(False)
            self._correction_btn.setVisible(False)
            self._notes_btn.setEnabled(False)
            self._lifecycle_hint_label.setText("Переходы жизненного цикла недоступны: турнир не выбран.")
            return

        current_status = str(self._current_tournament.get("status") or TournamentStatus.DRAFT.value)
        is_published = current_status == TournamentStatus.PUBLISHED.value

        self._correction_btn.setVisible(is_published)
        self._correction_btn.setEnabled(is_published)
        self._correction_btn.setToolTip(
            "Единственная точка входа для изменения опубликованного турнира."
            if is_published
            else ""
        )

        if is_published:
            self._recalc_btn.setEnabled(False)
            self._recalc_btn.setToolTip(
                "Для опубликованного турнира используйте операцию «Коррекция»."
            )
        else:
            self._recalc_btn.setEnabled(True)
            self._recalc_btn.setToolTip("")

        disabled_messages: list[str] = []
        for button, target_status in action_buttons:
            if is_published:
                button.setEnabled(False)
                button.setToolTip("Для опубликованного турнира доступна только операция «Коррекция».")
                disabled_messages.append(
                    f"{button.text()}: отключено для опубликованного турнира; используйте «Коррекция»."
                )
                continue
            reason = self._transition_block_reason(current_status, target_status)
            if reason:
                button.setEnabled(False)
                button.setToolTip(reason)
                disabled_messages.append(f"{button.text()}: {reason}")
            else:
                button.setEnabled(True)
                button.setToolTip("")
        self._lifecycle_hint_label.setText(
            "\n".join(disabled_messages) if disabled_messages else "Все переходы статусов доступны."
        )

    def _open_tournament_notes(self) -> None:
        if not self._current_tournament:
            QMessageBox.warning(self, "Заметки", "Турнир не выбран.")
            return
        dialog = EntityNotesDialog(
            connection=self._connection,
            entity_type="tournament",
            entity_id=str(self._current_tournament["id"]),
            defaults=EntityNoteDefaults(
                note_type="tournament_note",
                visibility="internal_service",
            ),
            parent=self,
        )
        dialog.exec()

    def _transition_block_reason(self, current_status: str, target_status: str) -> str | None:
        if current_status == target_status:
            return "Турнир уже находится в этом статусе."
        allowed = sorted(allowed_targets(current_status))
        if target_status in allowed:
            return None
        allowed_labels = ", ".join(tournament_status_label(status) for status in allowed) if allowed else "нет доступных переходов"
        return f"Недоступно из статуса «{tournament_status_label(current_status)}». Разрешено: {allowed_labels}."

    def _transition_tournament(self, target_status: str, action_title: str) -> None:
        if not self._current_tournament:
            QMessageBox.warning(self, action_title, "Турнир не выбран.")
            return
        tournament_id = int(self._current_tournament["id"])
        if target_status == TournamentStatus.PUBLISHED.value:
            preview = build_league_transfer_preview(
                connection=self._connection,
                tournament_id=tournament_id,
            )
            if preview.available and preview.rows:
                preview_lines = [
                    f"{row.fio}: {row.from_league_code or '-'} -> {row.to_league_code}"
                    for row in preview.rows[:5]
                ]
                if len(preview.rows) > 5:
                    preview_lines.append(f"... и ещё {len(preview.rows) - 5}")
                confirm = confirm_yes_no(
                    self,
                    action_title,
                    (
                        f"Будет зафиксировано переходов между лигами: {len(preview.rows)}.\n\n"
                        + "\n".join(preview_lines)
                        + "\n\nПродолжить публикацию?"
                    ),
                )
                if not confirm:
                    return
        transition_result = transition_tournament_status(
            connection=self._connection,
            tournament_id=tournament_id,
            to_status=target_status,
            context={"actor": "tournaments_view"},
        )
        if not transition_result.get("ok"):
            error_payload = transition_result.get("error") or {}
            message = str(error_payload.get("message") or "Не удалось изменить статус турнира.")
            details = error_payload.get("details")
            if isinstance(details, dict) and details.get("requirements"):
                requirements = details["requirements"]
                if isinstance(requirements, dict):
                    message = (
                        f"{message}\n"
                        f"Требования: причина={requirements.get('reason')}, "
                        f"точка восстановления={requirements.get('restore')}, аудит={requirements.get('audit')}"
                    )
            self._audit_log_service.log_event(
                ERROR,
                "Ошибка изменения статуса турнира",
                f"{message}; детали={details}",
                level="error",
                context={"tournament_id": tournament_id, "to_status": target_status},
            )
            QMessageBox.warning(self, action_title, message)
            self._refresh_lifecycle_controls()
            return

        self.refresh_latest_tournament(tournament_id)
        QMessageBox.information(self, action_title, f"Статус турнира обновлен: {tournament_status_label(target_status)}.")

    def _start_correction(self) -> None:
        if not self._current_tournament:
            QMessageBox.warning(self, "Коррекция", "Турнир не выбран.")
            return
        tournament_id = int(self._current_tournament["id"])
        reason, accepted = QInputDialog.getText(
            self,
            "Коррекция опубликованного турнира",
            "Укажите причину коррекции:",
        )
        if not accepted:
            return
        normalized_reason = reason.strip()
        if not normalized_reason:
            QMessageBox.warning(self, "Коррекция", "Причина обязательна.")
            return

        try:
            correction_result = correct_tournament(
                connection=self._connection,
                tournament_id=tournament_id,
                reason=normalized_reason,
                actor="tournaments_view",
            )
        except TournamentCorrectionError as exc:
            QMessageBox.warning(self, "Коррекция", str(exc))
            return

        self.refresh_latest_tournament(tournament_id)
        QMessageBox.information(
            self,
            "Коррекция",
            (
                "Коррекция применена.\n"
                f"Статус: {correction_result['to_status']}\n"
                f"Пересчитано результатов: {correction_result['results_recalculated']}"
            ),
        )

    def _create_manual_adult_tournament(self) -> None:
        dialog = ManualTournamentDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            payload = dialog.form_data()
            report = create_manual_adult_tournament(
                connection=self._connection,
                tournament_name=payload.tournament_name,
                tournament_date=payload.tournament_date,
                league_code=payload.league_code,
                rows=payload.rows,
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Взрослый турнир", str(exc))
            return

        self.refresh_latest_tournament(report.tournament_id)
        message_lines = [
            f"Создан черновик взрослого турнира: {report.tournament_name}",
            f"Импортировано строк: {report.imported_rows}",
            f"Пропущено строк: {report.skipped_rows}",
        ]
        if report.warnings:
            message_lines.append("\n".join(report.warnings[:3]))
        QMessageBox.information(self, "Взрослый турнир", "\n".join(message_lines))

    def _build_export_header(self) -> list[str]:
        if not self._current_tournament:
            return []
        name = self._current_tournament.get("name") or "Название не указано"
        date_label = self._current_tournament.get("date") or "дата не указана"
        category_label = (
            display_category_label(self._current_tournament.get("category_code"))
            if self._current_tournament.get("category_code")
            else "категория не указана"
        )
        return [
            "Протокол турнира",
            f"Турнир: {name}",
            f"Дата: {date_label}",
            f"Категория: {category_label}",
            "N: 6",
        ]

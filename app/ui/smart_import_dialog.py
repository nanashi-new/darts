from __future__ import annotations

from uuid import uuid4

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
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

from app.db.database import get_connection
from app.services.import_modes import (
    import_full,
    import_multi_tournament,
    import_players_only,
    import_update_players,
)
from app.services.import_pipeline import parse_tables_from_file
from app.services.import_xlsx import TableBlock


class SmartImportDialog(QDialog):
    """Dialog for smart import with mode selection."""

    def __init__(self, parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(parent)
        self.setWindowTitle("Умный импорт")
        self.resize(700, 550)

        self._blocks: list[TableBlock] = []
        self._file_path: str = ""

        layout = QVBoxLayout(self)

        # File picker
        file_row = QHBoxLayout()
        self._select_file_button = QPushButton("Выбрать файл", self)
        self._select_file_button.clicked.connect(self._on_select_file)
        file_row.addWidget(self._select_file_button)
        self._file_label = QLabel("Файл не выбран", self)
        self._file_label.setWordWrap(True)
        file_row.addWidget(self._file_label, 1)
        layout.addLayout(file_row)

        # Preview list
        layout.addWidget(QLabel("Найденные таблицы:", self))
        self._preview_list = QListWidget(self)
        layout.addWidget(self._preview_list)

        # Mode selector
        layout.addWidget(QLabel("Режим импорта:", self))
        self._mode_combo = QComboBox(self)
        self._mode_combo.addItems([
            "Полный импорт",
            "Только игроки",
            "Обновить данные игроков",
            "Несколько турниров",
        ])
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        layout.addWidget(self._mode_combo)

        # Tournament name (modes 0, 3)
        self._name_label = QLabel("Название турнира:", self)
        layout.addWidget(self._name_label)
        self._tournament_name_input = QLineEdit(self)
        self._tournament_name_input.setPlaceholderText("Введите название турнира")
        layout.addWidget(self._tournament_name_input)

        # Tournament date (modes 0, 3)
        self._date_label = QLabel("Дата турнира:", self)
        layout.addWidget(self._date_label)
        self._tournament_date_input = QDateEdit(self)
        self._tournament_date_input.setCalendarPopup(True)
        self._tournament_date_input.setDate(QDate.currentDate())
        self._tournament_date_input.setDisplayFormat("dd.MM.yyyy")
        layout.addWidget(self._tournament_date_input)

        # Checkboxes
        self._auto_register_checkbox = QCheckBox(
            "Авто-регистрация новых игроков", self
        )
        self._auto_register_checkbox.setChecked(True)
        layout.addWidget(self._auto_register_checkbox)

        self._auto_coach_checkbox = QCheckBox(
            "Авто-заполнение тренера из файла", self
        )
        self._auto_coach_checkbox.setChecked(True)
        layout.addWidget(self._auto_coach_checkbox)

        # Execute button
        self._execute_button = QPushButton("Выполнить", self)
        self._execute_button.clicked.connect(self._on_execute)
        layout.addWidget(self._execute_button)

        # Result label
        self._result_label = QLabel("", self)
        self._result_label.setWordWrap(True)
        self._result_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self._result_label)

        # Initial state
        self._on_mode_changed(0)

    def _on_mode_changed(self, index: int) -> None:
        show_tournament_fields = index in (0, 3)
        self._name_label.setVisible(show_tournament_fields)
        self._tournament_name_input.setVisible(show_tournament_fields)
        self._tournament_name_input.setEnabled(show_tournament_fields)
        self._date_label.setVisible(show_tournament_fields)
        self._tournament_date_input.setVisible(show_tournament_fields)
        self._tournament_date_input.setEnabled(show_tournament_fields)

    def _on_select_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выбрать файл",
            "",
            "Файлы данных (*.xlsx *.docx *.pdf)",
        )
        if not file_path:
            return

        self._file_path = file_path
        self._file_label.setText(file_path)

        try:
            self._blocks = parse_tables_from_file(file_path)
        except Exception as exc:
            QMessageBox.warning(self, "Ошибка", f"Не удалось разобрать файл:\n{exc}")
            self._blocks = []

        self._preview_list.clear()
        for block in self._blocks:
            text = f"{block.sheet_name}: {len(block.rows)} строк"
            self._preview_list.addItem(text)

        if not self._blocks:
            self._preview_list.addItem("Таблицы не найдены")

    def _on_execute(self) -> None:
        if not self._blocks:
            QMessageBox.warning(
                self, "Умный импорт", "Сначала выберите файл с данными."
            )
            return

        mode = self._mode_combo.currentIndex()
        connection = get_connection()

        try:
            if mode == 0:
                self._execute_full_import(connection)
            elif mode == 1:
                self._execute_players_only(connection)
            elif mode == 2:
                self._execute_update_players(connection)
            elif mode == 3:
                self._execute_multi_tournament(connection)
        except Exception as exc:
            QMessageBox.warning(self, "Ошибка импорта", str(exc))

    def _execute_full_import(self, connection: object) -> None:
        tournament_name = self._tournament_name_input.text().strip()
        if not tournament_name:
            QMessageBox.warning(self, "Умный импорт", "Введите название турнира.")
            return
        tournament_date = self._tournament_date_input.date().toString("yyyy-MM-dd")
        operation_group_id = uuid4().hex

        report = import_full(
            connection=connection,  # type: ignore[arg-type]
            blocks=self._blocks,
            tournament_name=tournament_name,
            tournament_date=tournament_date,
            category_code=None,
            is_adult_mode=False,
            source_files=[self._file_path],
            player_match_resolver=None,
            operation_group_id=operation_group_id,
        )
        self._result_label.setText(
            f"Импорт завершен.\n"
            f"Турнир: {report.tournament_name}\n"
            f"Импортировано строк: {report.imported_rows}\n"
            f"Пропущено: {report.skipped_rows}\n"
            f"Предупреждений: {len(report.warnings)}"
        )

    def _execute_players_only(self, connection: object) -> None:
        report = import_players_only(
            connection=connection,  # type: ignore[arg-type]
            blocks=self._blocks,
        )
        self._result_label.setText(
            f"Импорт игроков завершен.\n"
            f"Создано: {report.created}\n"
            f"Уже существуют: {report.existing}"
        )

    def _execute_update_players(self, connection: object) -> None:
        report = import_update_players(
            connection=connection,  # type: ignore[arg-type]
            blocks=self._blocks,
        )
        self._result_label.setText(
            f"Обновление игроков завершено.\n"
            f"Создано: {report.created}\n"
            f"Обновлено: {report.updated}\n"
            f"Без изменений: {report.unchanged}"
        )

    def _execute_multi_tournament(self, connection: object) -> None:
        base_name = self._tournament_name_input.text().strip()
        if not base_name:
            QMessageBox.warning(self, "Умный импорт", "Введите базовое название турнира.")
            return
        tournament_date = self._tournament_date_input.date().toString("yyyy-MM-dd")
        operation_group_id = uuid4().hex

        reports = import_multi_tournament(
            connection=connection,  # type: ignore[arg-type]
            blocks=self._blocks,
            base_name=base_name,
            tournament_date=tournament_date,
            is_adult_mode=False,
            source_files=[self._file_path],
            player_match_resolver=None,
            operation_group_id=operation_group_id,
        )
        total_imported = sum(r.imported_rows for r in reports)
        total_skipped = sum(r.skipped_rows for r in reports)
        self._result_label.setText(
            f"Мульти-импорт завершен.\n"
            f"Турниров создано: {len(reports)}\n"
            f"Всего импортировано строк: {total_imported}\n"
            f"Всего пропущено: {total_skipped}"
        )

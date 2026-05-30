from __future__ import annotations

from datetime import date

from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.db.database import get_connection
from app.db.repositories import PlayerRepository
from app.services.coach_tasks import (
    CoachTaskRecord,
    complete_coach_task,
    delete_coach_task,
    list_coach_tasks,
    list_overdue_tasks,
)
from app.services.training_plans import (
    TrainingPlanRecord,
    delete_training_plan,
    list_training_plans,
)
from app.ui.coach_task_dialog import CoachTaskDialog
from app.ui.labels import (
    COACH_TASK_PRIORITY_LABELS,
    COACH_TASK_STATUS_LABELS,
    coach_task_priority_label,
    coach_task_status_label,
    training_plan_status_label,
)
from app.ui.training_plan_dialog import TrainingPlanDialog


class CoachView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._connection = get_connection()
        self._task_rows: list[CoachTaskRecord] = []
        self._plan_rows: list[TrainingPlanRecord] = []

        layout = QVBoxLayout(self)

        self._tabs = QTabWidget(self)
        self._tabs.addTab(self._build_tasks_tab(), "Задачи")
        self._tabs.addTab(self._build_plans_tab(), "Планы")
        self._tabs.addTab(self._build_dashboard_tab(), "Сводка")
        self._tabs.currentChanged.connect(self._on_subtab_changed)
        layout.addWidget(self._tabs)

        self._refresh_tasks()
        self._refresh_plans()
        self._refresh_dashboard()

    # ─── Tasks sub-tab ──────────────────────────────────────────

    def _build_tasks_tab(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)

        # Filters
        filters = QHBoxLayout()

        self.task_status_filter = QComboBox(widget)
        self.task_status_filter.addItem("Все", None)
        for value, label in COACH_TASK_STATUS_LABELS.items():
            self.task_status_filter.addItem(label, value)
        self.task_status_filter.currentIndexChanged.connect(self._on_task_filters_changed)

        self.task_priority_filter = QComboBox(widget)
        self.task_priority_filter.addItem("Все", None)
        for value, label in COACH_TASK_PRIORITY_LABELS.items():
            self.task_priority_filter.addItem(label, value)
        self.task_priority_filter.currentIndexChanged.connect(self._on_task_filters_changed)

        self.task_player_filter = QComboBox(widget)
        self.task_player_filter.addItem("Все", None)
        self._load_player_filter(self.task_player_filter)
        self.task_player_filter.currentIndexChanged.connect(self._on_task_filters_changed)

        self.task_search_input = QLineEdit(widget)
        self.task_search_input.setPlaceholderText("Поиск по задачам")
        self.task_search_input.textChanged.connect(self._on_task_filters_changed)

        filters.addWidget(self.task_status_filter)
        filters.addWidget(self.task_priority_filter)
        filters.addWidget(self.task_player_filter)
        filters.addWidget(self.task_search_input)
        layout.addLayout(filters)

        # Table
        self.tasks_table = QTableWidget(0, 7, widget)
        self.tasks_table.setHorizontalHeaderLabels(
            ["Статус", "Приоритет", "Игрок", "Задача", "Срок", "Категория", "Создано"]
        )
        self.tasks_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tasks_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tasks_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tasks_table.itemDoubleClicked.connect(lambda *_args: self._edit_task())
        layout.addWidget(self.tasks_table)

        # Actions
        actions = QHBoxLayout()
        self.create_task_button = QPushButton("Создать задачу", widget)
        self.create_task_button.setToolTip("Создать новую задачу тренера.")
        self.create_task_button.clicked.connect(self._create_task)

        self.edit_task_button = QPushButton("Редактировать", widget)
        self.edit_task_button.setToolTip("Редактировать выбранную задачу.")
        self.edit_task_button.clicked.connect(self._edit_task)

        self.complete_task_button = QPushButton("Завершить", widget)
        self.complete_task_button.setToolTip("Пометить выбранную задачу как выполненную.")
        self.complete_task_button.clicked.connect(self._complete_task)

        self.delete_task_button = QPushButton("Удалить", widget)
        self.delete_task_button.setToolTip("Удалить выбранную задачу.")
        self.delete_task_button.clicked.connect(self._delete_task)

        actions.addWidget(self.create_task_button)
        actions.addWidget(self.edit_task_button)
        actions.addWidget(self.complete_task_button)
        actions.addWidget(self.delete_task_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        return widget

    # ─── Plans sub-tab ──────────────────────────────────────────

    def _build_plans_tab(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)

        # Table
        self.plans_table = QTableWidget(0, 6, widget)
        self.plans_table.setHorizontalHeaderLabels(
            ["Статус", "Игрок", "Название", "Цель", "Период", "Создано"]
        )
        self.plans_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.plans_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.plans_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.plans_table.itemDoubleClicked.connect(lambda *_args: self._edit_plan())
        layout.addWidget(self.plans_table)

        # Actions
        actions = QHBoxLayout()
        self.create_plan_button = QPushButton("Создать план", widget)
        self.create_plan_button.setToolTip("Создать новый план тренировок.")
        self.create_plan_button.clicked.connect(self._create_plan)

        self.edit_plan_button = QPushButton("Редактировать", widget)
        self.edit_plan_button.setToolTip("Редактировать выбранный план.")
        self.edit_plan_button.clicked.connect(self._edit_plan)

        self.delete_plan_button = QPushButton("Удалить", widget)
        self.delete_plan_button.setToolTip("Удалить выбранный план.")
        self.delete_plan_button.clicked.connect(self._delete_plan)

        actions.addWidget(self.create_plan_button)
        actions.addWidget(self.edit_plan_button)
        actions.addWidget(self.delete_plan_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        return widget

    # ─── Dashboard sub-tab ──────────────────────────────────────

    def _build_dashboard_tab(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)

        # Summary stats
        stats_group = QGroupBox("Статистика", widget)
        stats_layout = QVBoxLayout(stats_group)

        self.stat_open_tasks_label = QLabel("Открытых задач: 0", stats_group)
        self.stat_overdue_label = QLabel("Просроченных: 0", stats_group)
        self.stat_urgent_label = QLabel("Срочных: 0", stats_group)
        self.stat_done_month_label = QLabel("Выполнено за месяц: 0", stats_group)
        self.stat_active_plans_label = QLabel("Активных планов: 0", stats_group)

        stats_layout.addWidget(self.stat_open_tasks_label)
        stats_layout.addWidget(self.stat_overdue_label)
        stats_layout.addWidget(self.stat_urgent_label)
        stats_layout.addWidget(self.stat_done_month_label)
        stats_layout.addWidget(self.stat_active_plans_label)
        layout.addWidget(stats_group)

        # Upcoming tasks mini-table
        upcoming_group = QGroupBox("Ближайшие задачи", widget)
        upcoming_layout = QVBoxLayout(upcoming_group)
        self.upcoming_table = QTableWidget(0, 4, widget)
        self.upcoming_table.setHorizontalHeaderLabels(["Приоритет", "Игрок", "Задача", "Срок"])
        self.upcoming_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.upcoming_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.upcoming_table.verticalHeader().setVisible(False)
        upcoming_layout.addWidget(self.upcoming_table)
        layout.addWidget(upcoming_group)

        # Overdue tasks mini-table
        overdue_group = QGroupBox("Просроченные", widget)
        overdue_layout = QVBoxLayout(overdue_group)
        self.overdue_table = QTableWidget(0, 4, widget)
        self.overdue_table.setHorizontalHeaderLabels(["Приоритет", "Игрок", "Задача", "Срок"])
        self.overdue_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.overdue_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.overdue_table.verticalHeader().setVisible(False)
        overdue_layout.addWidget(self.overdue_table)
        layout.addWidget(overdue_group)

        layout.addStretch(1)
        return widget

    # ─── Filters logic ──────────────────────────────────────────

    def _load_player_filter(self, combo: QComboBox) -> None:
        try:
            repo = PlayerRepository(self._connection)
            players = repo.list()
            for p in players:
                fio = " ".join(
                    part
                    for part in [
                        str(p.get("last_name") or "").strip(),
                        str(p.get("first_name") or "").strip(),
                        str(p.get("middle_name") or "").strip(),
                    ]
                    if part
                )
                combo.addItem(fio, int(p["id"]))
        except Exception:  # noqa: BLE001
            pass

    def _on_task_filters_changed(self, *_args: object) -> None:
        self._refresh_tasks()

    def _on_subtab_changed(self, index: int) -> None:
        if index == 2:
            self._refresh_dashboard()

    # ─── Refresh ────────────────────────────────────────────────

    def _refresh_tasks(self) -> None:
        status_filter = self.task_status_filter.currentData()
        priority_filter = self.task_priority_filter.currentData()
        player_filter = self.task_player_filter.currentData()
        search_text = self.task_search_input.text().strip().lower()

        include_done = status_filter in ("done", "cancelled")
        tasks = list_coach_tasks(
            connection=self._connection,
            status=str(status_filter) if status_filter else None,
            priority=str(priority_filter) if priority_filter else None,
            player_id=int(player_filter) if player_filter is not None else None,
            include_done=include_done,
        )

        if search_text:
            tasks = [
                t for t in tasks
                if search_text in t.title.lower()
                or search_text in (t.player_fio or "").lower()
                or search_text in (t.category or "").lower()
            ]

        self._task_rows = tasks
        self.tasks_table.setRowCount(0)
        for task in tasks:
            row_index = self.tasks_table.rowCount()
            self.tasks_table.insertRow(row_index)
            values = [
                coach_task_status_label(task.status),
                coach_task_priority_label(task.priority),
                task.player_fio or "",
                task.title,
                task.due_date or "",
                task.category or "",
                str(task.created_at).replace("T", " ")[:19],
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                self.tasks_table.setItem(row_index, col, item)

    def _refresh_plans(self) -> None:
        plans = list_training_plans(connection=self._connection)
        self._plan_rows = plans
        self.plans_table.setRowCount(0)
        for plan in plans:
            row_index = self.plans_table.rowCount()
            self.plans_table.insertRow(row_index)
            period = ""
            if plan.start_date and plan.end_date:
                period = f"{plan.start_date} - {plan.end_date}"
            elif plan.start_date:
                period = f"с {plan.start_date}"
            elif plan.end_date:
                period = f"до {plan.end_date}"
            values = [
                training_plan_status_label(plan.status),
                plan.player_fio,
                plan.title,
                plan.goal or "",
                period,
                str(plan.created_at).replace("T", " ")[:19],
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                self.plans_table.setItem(row_index, col, item)

    def _refresh_dashboard(self) -> None:
        # Skip refresh if the dashboard sub-tab is not currently active
        if self._tabs.currentIndex() != 2:
            return
        # Open tasks
        open_tasks = list_coach_tasks(connection=self._connection, status="open")
        in_progress_tasks = list_coach_tasks(connection=self._connection, status="in_progress")
        all_open = open_tasks + in_progress_tasks
        self.stat_open_tasks_label.setText(f"Открытых задач: {len(all_open)}")

        # Overdue
        overdue = list_overdue_tasks(connection=self._connection)
        overdue_count = len(overdue)
        overdue_text = f"Просроченных: {overdue_count}"
        if overdue_count > 0:
            self.stat_overdue_label.setStyleSheet("color: red;")
        else:
            self.stat_overdue_label.setStyleSheet("")
        self.stat_overdue_label.setText(overdue_text)

        # Urgent
        urgent_tasks = list_coach_tasks(connection=self._connection, priority="urgent")
        self.stat_urgent_label.setText(f"Срочных: {len(urgent_tasks)}")

        # Done this month
        today = date.today()
        first_of_month = today.replace(day=1)
        done_tasks = list_coach_tasks(
            connection=self._connection, status="done", include_done=True
        )
        done_this_month = [
            t for t in done_tasks
            if t.completed_at and t.completed_at >= first_of_month.isoformat()
        ]
        self.stat_done_month_label.setText(f"Выполнено за месяц: {len(done_this_month)}")

        # Active plans
        active_plans = list_training_plans(connection=self._connection, status="active")
        self.stat_active_plans_label.setText(f"Активных планов: {len(active_plans)}")

        # Upcoming mini-table (top 5 tasks with due_date in the future, sorted by date)
        today_str = today.isoformat()
        upcoming = sorted(
            [t for t in all_open if t.due_date and t.due_date >= today_str],
            key=lambda t: t.due_date or "",
        )[:5]
        self.upcoming_table.setRowCount(0)
        for task in upcoming:
            row_index = self.upcoming_table.rowCount()
            self.upcoming_table.insertRow(row_index)
            for col, value in enumerate([
                coach_task_priority_label(task.priority),
                task.player_fio or "",
                task.title,
                task.due_date or "",
            ]):
                self.upcoming_table.setItem(row_index, col, QTableWidgetItem(str(value)))

        # Overdue mini-table
        self.overdue_table.setRowCount(0)
        for task in overdue:
            row_index = self.overdue_table.rowCount()
            self.overdue_table.insertRow(row_index)
            for col, value in enumerate([
                coach_task_priority_label(task.priority),
                task.player_fio or "",
                task.title,
                task.due_date or "",
            ]):
                self.overdue_table.setItem(row_index, col, QTableWidgetItem(str(value)))

    # ─── Task actions ───────────────────────────────────────────

    def _create_task(self) -> None:
        dialog = CoachTaskDialog(connection=self._connection, parent=self)
        if dialog.exec() != CoachTaskDialog.DialogCode.Accepted:
            return
        from app.services.coach_tasks import create_coach_task
        data = dialog.form_data()
        create_coach_task(
            connection=self._connection,
            player_id=data.player_id,
            title=data.title,
            description=data.description,
            due_date=data.due_date,
            priority=data.priority,
            category=data.category,
        )
        self._refresh_tasks()
        self._refresh_dashboard()

    def _edit_task(self) -> None:
        row = self.tasks_table.currentRow()
        if row < 0 or row >= len(self._task_rows):
            QMessageBox.information(self, "Тренер", "Сначала выберите задачу.")
            return
        record = self._task_rows[row]
        dialog = CoachTaskDialog(
            connection=self._connection, edit_record=record, parent=self
        )
        if dialog.exec() != CoachTaskDialog.DialogCode.Accepted:
            return
        from app.services.coach_tasks import update_coach_task
        data = dialog.form_data()
        update_coach_task(
            record.id,
            connection=self._connection,
            player_id=data.player_id,
            title=data.title,
            description=data.description,
            due_date=data.due_date,
            priority=data.priority,
            category=data.category,
            status=data.status,
        )
        self._refresh_tasks()
        self._refresh_dashboard()

    def _complete_task(self) -> None:
        row = self.tasks_table.currentRow()
        if row < 0 or row >= len(self._task_rows):
            QMessageBox.information(self, "Тренер", "Сначала выберите задачу.")
            return
        record = self._task_rows[row]
        complete_coach_task(record.id, connection=self._connection)
        self._refresh_tasks()
        self._refresh_dashboard()

    def _delete_task(self) -> None:
        row = self.tasks_table.currentRow()
        if row < 0 or row >= len(self._task_rows):
            QMessageBox.information(self, "Тренер", "Сначала выберите задачу.")
            return
        record = self._task_rows[row]
        reply = QMessageBox.question(
            self,
            "Удаление задачи",
            f"Удалить задачу '{record.title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_coach_task(connection=self._connection, task_id=record.id)
            self._refresh_tasks()
            self._refresh_dashboard()

    # ─── Plan actions ───────────────────────────────────────────

    def _create_plan(self) -> None:
        dialog = TrainingPlanDialog(connection=self._connection, parent=self)
        if dialog.exec() != TrainingPlanDialog.DialogCode.Accepted:
            return
        from app.services.training_plans import create_training_plan
        data = dialog.form_data()
        create_training_plan(
            connection=self._connection,
            player_id=data.player_id,
            title=data.title,
            description=data.description,
            goal=data.goal,
            start_date=data.start_date,
            end_date=data.end_date,
            exercises=data.exercises,
        )
        self._refresh_plans()
        self._refresh_dashboard()

    def _edit_plan(self) -> None:
        row = self.plans_table.currentRow()
        if row < 0 or row >= len(self._plan_rows):
            QMessageBox.information(self, "Тренер", "Сначала выберите план.")
            return
        record = self._plan_rows[row]
        dialog = TrainingPlanDialog(
            connection=self._connection, edit_record=record, parent=self
        )
        if dialog.exec() != TrainingPlanDialog.DialogCode.Accepted:
            return
        from app.services.training_plans import update_training_plan
        data = dialog.form_data()
        update_training_plan(
            record.id,
            connection=self._connection,
            player_id=data.player_id,
            title=data.title,
            description=data.description,
            goal=data.goal,
            start_date=data.start_date,
            end_date=data.end_date,
            status=data.status,
            exercises=data.exercises,
        )
        self._refresh_plans()
        self._refresh_dashboard()

    def _delete_plan(self) -> None:
        row = self.plans_table.currentRow()
        if row < 0 or row >= len(self._plan_rows):
            QMessageBox.information(self, "Тренер", "Сначала выберите план.")
            return
        record = self._plan_rows[row]
        reply = QMessageBox.question(
            self,
            "Удаление плана",
            f"Удалить план '{record.title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_training_plan(connection=self._connection, plan_id=record.id)
            self._refresh_plans()
            self._refresh_dashboard()

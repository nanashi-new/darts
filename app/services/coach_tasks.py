from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.db.repositories import CoachTaskRepository
from app.services.audit_log import (
    AuditLogService,
    COACH_TASK_CREATED,
    COACH_TASK_DELETED,
    COACH_TASK_UPDATED,
    COACH_TASK_COMPLETED,
)


@dataclass(frozen=True)
class CoachTaskRecord:
    id: int
    player_id: int | None
    player_fio: str
    title: str
    description: str | None
    due_date: str | None
    status: str
    priority: str
    category: str | None
    created_at: str
    updated_at: str
    completed_at: str | None


def create_coach_task(
    *,
    connection: Any,
    player_id: int | None = None,
    title: str,
    description: str | None = None,
    due_date: str | None = None,
    status: str = "open",
    priority: str = "normal",
    category: str | None = None,
) -> int:
    normalized_title = title.strip()
    if not normalized_title:
        raise ValueError("Укажите название задачи.")

    repo = CoachTaskRepository(connection)
    task_id = repo.create(
        {
            "player_id": player_id,
            "title": normalized_title,
            "description": (description or "").strip() or None,
            "due_date": due_date,
            "status": status,
            "priority": priority,
            "category": (category or "").strip() or None,
        }
    )
    AuditLogService(connection).log_event(
        COACH_TASK_CREATED,
        "Создана задача тренера",
        f"Задача ID: {task_id}; заголовок={normalized_title}",
        context={
            "task_id": task_id,
            "player_id": player_id,
            "priority": priority,
            "status": status,
        },
        entity_type="player",
        entity_id=str(player_id) if player_id else None,
        source="coach_tasks",
    )
    return task_id


def update_coach_task(
    task_id: int,
    *,
    connection: Any,
    **kwargs: Any,
) -> None:
    repo = CoachTaskRepository(connection)
    data: dict[str, Any] = {}
    allowed = [
        "player_id", "title", "description", "due_date",
        "status", "priority", "category",
    ]
    for key in allowed:
        if key in kwargs:
            value = kwargs[key]
            if key == "title":
                value = (str(value) if value else "").strip()
                if not value:
                    raise ValueError("Укажите название задачи.")
            elif key in ("description", "category"):
                value = (str(value) if value else "").strip() or None
            data[key] = value
    repo.update(task_id, data)
    AuditLogService(connection).log_event(
        COACH_TASK_UPDATED,
        "Обновлена задача тренера",
        f"Задача ID: {task_id}",
        context={"task_id": task_id, "updated_fields": list(data.keys())},
        entity_type="player",
        entity_id=str(kwargs.get("player_id")) if kwargs.get("player_id") else None,
        source="coach_tasks",
    )


def complete_coach_task(task_id: int, *, connection: Any) -> None:
    repo = CoachTaskRepository(connection)
    repo.complete(task_id)
    AuditLogService(connection).log_event(
        COACH_TASK_COMPLETED,
        "Задача тренера выполнена",
        f"Задача ID: {task_id}",
        context={"task_id": task_id},
        source="coach_tasks",
    )


def list_coach_tasks(
    *,
    connection: Any,
    status: str | None = None,
    priority: str | None = None,
    player_id: int | None = None,
    include_done: bool = False,
) -> list[CoachTaskRecord]:
    repo = CoachTaskRepository(connection)
    return [
        _row_to_record(row)
        for row in repo.list_all(
            status=status,
            priority=priority,
            player_id=player_id,
            include_done=include_done,
        )
    ]


def list_player_coach_tasks(
    *,
    connection: Any,
    player_id: int,
    include_done: bool = False,
) -> list[CoachTaskRecord]:
    repo = CoachTaskRepository(connection)
    return [
        _row_to_record(row)
        for row in repo.list_for_player(player_id, include_done=include_done)
    ]


def list_overdue_tasks(*, connection: Any) -> list[CoachTaskRecord]:
    repo = CoachTaskRepository(connection)
    return [_row_to_record(row) for row in repo.list_overdue()]


def get_coach_task(*, connection: Any, task_id: int) -> CoachTaskRecord | None:
    repo = CoachTaskRepository(connection)
    row = repo.get(task_id)
    if row is None:
        return None
    return _row_to_record(row)


def delete_coach_task(*, connection: Any, task_id: int) -> None:
    repo = CoachTaskRepository(connection)
    repo.delete(task_id)
    AuditLogService(connection).log_event(
        COACH_TASK_DELETED,
        "Удалена задача тренера",
        f"Задача ID: {task_id}",
        context={"task_id": task_id},
        source="coach_tasks",
    )


def _row_to_record(row: dict[str, Any]) -> CoachTaskRecord:
    fio = " ".join(
        part
        for part in [
            str(row.get("last_name") or "").strip(),
            str(row.get("first_name") or "").strip(),
            str(row.get("middle_name") or "").strip(),
        ]
        if part
    )
    player_id_raw = row.get("player_id")
    return CoachTaskRecord(
        id=int(row["id"]),
        player_id=int(player_id_raw) if player_id_raw is not None else None,
        player_fio=fio,
        title=str(row["title"]),
        description=str(row["description"]) if row.get("description") is not None else None,
        due_date=str(row["due_date"]) if row.get("due_date") is not None else None,
        status=str(row["status"]),
        priority=str(row["priority"]),
        category=str(row["category"]) if row.get("category") is not None else None,
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        completed_at=str(row["completed_at"]) if row.get("completed_at") is not None else None,
    )

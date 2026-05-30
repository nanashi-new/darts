from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.db.repositories import TrainingPlanRepository
from app.services.audit_log import (
    AuditLogService,
    TRAINING_PLAN_CREATED,
    TRAINING_PLAN_UPDATED,
)


@dataclass(frozen=True)
class TrainingPlanRecord:
    id: int
    player_id: int
    player_fio: str
    title: str
    description: str | None
    goal: str | None
    start_date: str | None
    end_date: str | None
    status: str
    exercises: list[Any]
    created_at: str
    updated_at: str


def create_training_plan(
    *,
    connection: Any,
    player_id: int,
    title: str,
    description: str | None = None,
    goal: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    status: str = "active",
    exercises: list[Any] | None = None,
) -> int:
    normalized_title = title.strip()
    if not normalized_title:
        raise ValueError("Укажите название плана тренировок.")

    exercises_list = exercises if exercises is not None else []
    exercises_json = json.dumps(exercises_list, ensure_ascii=False)

    repo = TrainingPlanRepository(connection)
    plan_id = repo.create(
        {
            "player_id": player_id,
            "title": normalized_title,
            "description": (description or "").strip() or None,
            "goal": (goal or "").strip() or None,
            "start_date": start_date,
            "end_date": end_date,
            "status": status,
            "exercises_json": exercises_json,
        }
    )
    AuditLogService(connection).log_event(
        TRAINING_PLAN_CREATED,
        "Создан план тренировок",
        f"План ID: {plan_id}; заголовок={normalized_title}",
        context={
            "plan_id": plan_id,
            "player_id": player_id,
            "status": status,
        },
        entity_type="player",
        entity_id=str(player_id),
        source="training_plans",
    )
    return plan_id


def update_training_plan(
    plan_id: int,
    *,
    connection: Any,
    **kwargs: Any,
) -> None:
    repo = TrainingPlanRepository(connection)
    data: dict[str, Any] = {}
    allowed = [
        "player_id", "title", "description", "goal",
        "start_date", "end_date", "status", "exercises",
    ]
    for key in allowed:
        if key in kwargs:
            value = kwargs[key]
            if key == "title":
                value = (str(value) if value else "").strip()
                if not value:
                    raise ValueError("Укажите название плана тренировок.")
                data["title"] = value
            elif key in ("description", "goal"):
                data[key] = (str(value) if value else "").strip() or None
            elif key == "exercises":
                exercises_list = value if value is not None else []
                data["exercises_json"] = json.dumps(exercises_list, ensure_ascii=False)
            else:
                data[key] = value
    repo.update(plan_id, data)
    AuditLogService(connection).log_event(
        TRAINING_PLAN_UPDATED,
        "Обновлен план тренировок",
        f"План ID: {plan_id}",
        context={"plan_id": plan_id, "updated_fields": list(data.keys())},
        entity_type="player",
        entity_id=str(kwargs.get("player_id")) if kwargs.get("player_id") else None,
        source="training_plans",
    )


def list_training_plans(
    *,
    connection: Any,
    status: str | None = None,
    player_id: int | None = None,
) -> list[TrainingPlanRecord]:
    repo = TrainingPlanRepository(connection)
    return [
        _row_to_record(row)
        for row in repo.list_all(status=status, player_id=player_id)
    ]


def list_player_training_plans(
    *,
    connection: Any,
    player_id: int,
    status: str | None = None,
) -> list[TrainingPlanRecord]:
    repo = TrainingPlanRepository(connection)
    return [
        _row_to_record(row)
        for row in repo.list_for_player(player_id, status=status)
    ]


def get_training_plan(*, connection: Any, plan_id: int) -> TrainingPlanRecord | None:
    repo = TrainingPlanRepository(connection)
    row = repo.get(plan_id)
    if row is None:
        return None
    return _row_to_record(row)


def delete_training_plan(*, connection: Any, plan_id: int) -> None:
    repo = TrainingPlanRepository(connection)
    repo.delete(plan_id)


def _row_to_record(row: dict[str, Any]) -> TrainingPlanRecord:
    fio = " ".join(
        part
        for part in [
            str(row.get("last_name") or "").strip(),
            str(row.get("first_name") or "").strip(),
            str(row.get("middle_name") or "").strip(),
        ]
        if part
    )
    exercises_raw = row.get("exercises_json")
    try:
        exercises = json.loads(str(exercises_raw or "[]"))
    except json.JSONDecodeError:
        exercises = []
    if not isinstance(exercises, list):
        exercises = []

    return TrainingPlanRecord(
        id=int(row["id"]),
        player_id=int(row["player_id"]),
        player_fio=fio,
        title=str(row["title"]),
        description=str(row["description"]) if row.get("description") is not None else None,
        goal=str(row["goal"]) if row.get("goal") is not None else None,
        start_date=str(row["start_date"]) if row.get("start_date") is not None else None,
        end_date=str(row["end_date"]) if row.get("end_date") is not None else None,
        status=str(row["status"]),
        exercises=exercises,
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )

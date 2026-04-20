from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.db.repositories import TrainingEntryRepository
from app.services.audit_log import AuditLogService, TRAINING_ENTRY_CREATED


@dataclass(frozen=True)
class TrainingEntryRecord:
    id: int
    player_id: int
    player_fio: str
    coach_name: str | None
    training_date: str
    session_type: str
    summary: str
    goals: str | None
    metrics: dict[str, object]
    related_tournament_id: int | None
    tournament_name: str | None
    next_action: str | None
    is_archived: bool
    created_at: str
    updated_at: str


def create_training_entry(
    *,
    connection,
    player_id: int,
    coach_name: str | None,
    training_date: str,
    session_type: str,
    summary: str,
    goals: str | None,
    metrics: dict[str, object] | None,
    related_tournament_id: int | None,
    next_action: str | None,
    is_archived: bool = False,
) -> int:
    normalized_summary = summary.strip()
    if not normalized_summary:
        raise ValueError("Training summary is required.")
    repository = TrainingEntryRepository(connection)
    entry_id = repository.create(
        {
            "player_id": player_id,
            "coach_name": (coach_name or "").strip() or None,
            "training_date": training_date,
            "session_type": session_type,
            "summary": normalized_summary,
            "goals": (goals or "").strip() or None,
            "metrics_json": json.dumps(metrics or {}, ensure_ascii=False),
            "related_tournament_id": related_tournament_id,
            "next_action": (next_action or "").strip() or None,
            "is_archived": is_archived,
        }
    )
    AuditLogService(connection).log_event(
        TRAINING_ENTRY_CREATED,
        "Training entry created",
        f"Training entry ID: {entry_id}; player_id={player_id}",
        context={
            "entry_id": entry_id,
            "player_id": player_id,
            "session_type": session_type,
            "training_date": training_date,
        },
        entity_type="player",
        entity_id=str(player_id),
        source="training_journal",
    )
    return entry_id


def list_player_training_entries(
    *,
    connection,
    player_id: int,
    include_archived: bool = False,
) -> list[TrainingEntryRecord]:
    repository = TrainingEntryRepository(connection)
    return [
        _row_to_record(row)
        for row in repository.list_for_player(
            player_id,
            include_archived=include_archived,
        )
    ]


def list_training_entries(
    *,
    connection,
    include_archived: bool = False,
    query: str | None = None,
) -> list[TrainingEntryRecord]:
    repository = TrainingEntryRepository(connection)
    return [
        _row_to_record(row)
        for row in repository.list_all(
            include_archived=include_archived,
            query=query,
        )
    ]


def _row_to_record(row: dict[str, Any]) -> TrainingEntryRecord:
    metrics_raw = row.get("metrics_json")
    try:
        metrics = json.loads(str(metrics_raw or "{}"))
    except json.JSONDecodeError:
        metrics = {}
    if not isinstance(metrics, dict):
        metrics = {}
    fio = " ".join(
        part
        for part in [
            str(row.get("last_name") or "").strip(),
            str(row.get("first_name") or "").strip(),
            str(row.get("middle_name") or "").strip(),
        ]
        if part
    )
    related_tournament_id_raw = row.get("related_tournament_id")
    return TrainingEntryRecord(
        id=int(row["id"]),
        player_id=int(row["player_id"]),
        player_fio=fio,
        coach_name=str(row["coach_name"]) if row.get("coach_name") is not None else None,
        training_date=str(row["training_date"]),
        session_type=str(row["session_type"]),
        summary=str(row["summary"]),
        goals=str(row["goals"]) if row.get("goals") is not None else None,
        metrics=metrics,
        related_tournament_id=(
            int(related_tournament_id_raw)
            if related_tournament_id_raw is not None
            else None
        ),
        tournament_name=(
            str(row["tournament_name"])
            if row.get("tournament_name") is not None
            else None
        ),
        next_action=str(row["next_action"]) if row.get("next_action") is not None else None,
        is_archived=bool(int(row["is_archived"] or 0)),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )

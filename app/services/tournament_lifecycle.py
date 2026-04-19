"""Service layer for tournament lifecycle transitions."""

from __future__ import annotations

import json
from typing import Any

from app.db.repositories import TournamentRepository
from app.domain.tournament_lifecycle import TournamentStatus, can_transition
from app.services.audit_log import (
    AuditLogService,
    TOURNAMENT_CORRECTED,
    TOURNAMENT_PUBLISHED,
    TOURNAMENT_UPDATED,
)


def transition_tournament_status(
    *,
    connection,
    tournament_id: int,
    to_status: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Change tournament status with UI-friendly structured errors."""

    tournament_repo = TournamentRepository(connection)
    audit_log_service = AuditLogService(connection)
    current = tournament_repo.get(tournament_id)
    if current is None:
        return {
            "ok": False,
            "error": {
                "code": "tournament_not_found",
                "message": "Турнир не найден.",
                "details": {"tournament_id": tournament_id},
            },
        }

    from_status = str(current.get("status") or TournamentStatus.DRAFT.value)
    payload = context or {}

    try:
        target_status = TournamentStatus(str(to_status).strip().lower()).value
    except ValueError:
        return {
            "ok": False,
            "error": {
                "code": "unknown_status",
                "message": "Неизвестный статус турнира.",
                "details": {"to_status": to_status},
            },
        }

    if not can_transition(from_status, target_status, payload):
        return {
            "ok": False,
            "error": {
                "code": "invalid_transition",
                "message": "Переход статуса запрещён правилами жизненного цикла.",
                "details": {
                    "from_status": from_status,
                    "to_status": target_status,
                    "requirements": {
                        "reason": "required for dangerous transitions",
                        "restore": "must be true for dangerous transitions",
                        "audit": "required for dangerous transitions",
                    },
                },
            },
        }

    actor = payload.get("actor")
    tournament_repo.set_status(
        tournament_id,
        target_status,
        actor=str(actor) if actor is not None else None,
        context=payload,
    )

    reason = str(payload.get("reason") or "").strip() or None
    source = str(payload.get("actor") or "").strip() or "tournament_lifecycle"
    operation_group_id = str(payload.get("operation_group_id") or "").strip() or None
    old_value_json = json.dumps({"status": from_status}, ensure_ascii=False)
    new_value_json = json.dumps({"status": target_status}, ensure_ascii=False)
    event_type = _resolve_tournament_event_type(from_status=from_status, to_status=target_status)
    audit_log_service.log_event(
        event_type,
        "Статус турнира изменён",
        f"Турнир ID: {tournament_id}; {from_status} -> {target_status}",
        context={
            "tournament_id": tournament_id,
            "from_status": from_status,
            "to_status": target_status,
            "reason": reason,
        },
        entity_type="tournament",
        entity_id=str(tournament_id),
        reason=reason,
        old_value_json=old_value_json,
        new_value_json=new_value_json,
        source=source,
        operation_group_id=operation_group_id,
    )

    snapshot_result = None
    transfer_result = None
    if target_status == TournamentStatus.PUBLISHED.value:
        from app.services.rating_snapshot import create_rating_snapshot_for_tournament_publish
        from app.services.league_transfer import record_league_transfers_for_tournament_publish

        snapshot_result = create_rating_snapshot_for_tournament_publish(
            connection=connection,
            tournament_id=tournament_id,
            n_value=6,
            operation_group_id=operation_group_id,
        )
        transfer_result = record_league_transfers_for_tournament_publish(
            connection=connection,
            tournament_id=tournament_id,
            operation_group_id=operation_group_id,
        )

    return {
        "ok": True,
        "data": {
            "tournament_id": tournament_id,
            "from_status": from_status,
            "to_status": target_status,
            "snapshot_created": bool(snapshot_result.created) if snapshot_result is not None else False,
            "snapshot_reason": snapshot_result.reason if snapshot_result is not None else None,
            "league_transfers_recorded": transfer_result.recorded_count if transfer_result is not None else 0,
        },
    }


def _resolve_tournament_event_type(*, from_status: str, to_status: str) -> str:
    if to_status == TournamentStatus.PUBLISHED.value:
        return TOURNAMENT_PUBLISHED
    if to_status == TournamentStatus.REVIEW.value and from_status in {
        TournamentStatus.PUBLISHED.value,
        TournamentStatus.ARCHIVED.value,
        TournamentStatus.CONFIRMED.value,
    }:
        return TOURNAMENT_CORRECTED
    return TOURNAMENT_UPDATED

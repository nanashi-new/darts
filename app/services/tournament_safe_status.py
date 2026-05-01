from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.domain.tournament_lifecycle import TournamentStatus
from app.services.restore_points import create_restore_point
from app.services.tournament_lifecycle import transition_tournament_status

_SUPPORTED_TARGETS = {
    TournamentStatus.ARCHIVED.value,
    TournamentStatus.CANCELED.value,
}
_RESTORE_STATUSES = {
    TournamentStatus.CONFIRMED.value,
    TournamentStatus.PUBLISHED.value,
}


def archive_or_cancel_tournament(
    *,
    connection,
    tournament_id: int,
    target_status: str,
    reason: str,
    actor: str | None = None,
    operation_group_id: str | None = None,
) -> dict[str, Any]:
    normalized_target = str(target_status or "").strip().lower()
    if normalized_target not in _SUPPORTED_TARGETS:
        return {
            "ok": False,
            "error": {
                "code": "unsupported_target_status",
                "message": "Поддерживаются только архивирование и отмена турнира.",
                "details": {"target_status": target_status},
            },
        }

    normalized_reason = str(reason or "").strip()
    if not normalized_reason:
        return {
            "ok": False,
            "error": {
                "code": "reason_required",
                "message": "Укажите причину операции.",
                "details": {"target_status": normalized_target},
            },
        }

    from app.db.repositories import TournamentRepository

    tournament_repo = TournamentRepository(connection)
    tournament = tournament_repo.get(tournament_id)
    if tournament is None:
        return {
            "ok": False,
            "error": {
                "code": "tournament_not_found",
                "message": "Турнир не найден.",
                "details": {"tournament_id": tournament_id},
            },
        }

    from_status = str(tournament.get("status") or TournamentStatus.DRAFT.value)
    operation_id = str(operation_group_id or "").strip() or f"safe-status-{uuid4().hex}"
    restore_point_created = False
    if from_status in _RESTORE_STATUSES:
        create_restore_point(
            connection=connection,
            title=f"Before tournament {normalized_target} #{tournament_id}",
            reason=f"tournament_{normalized_target}",
            source=actor or "tournament_safe_status",
            operation_group_id=operation_id,
        )
        restore_point_created = True

    transition_result = transition_tournament_status(
        connection=connection,
        tournament_id=tournament_id,
        to_status=normalized_target,
        context={
            "actor": actor or "tournament_safe_status",
            "reason": normalized_reason,
            "restore": restore_point_created,
            "audit": {
                "source": "tournament_safe_status",
                "safe_status": True,
            },
            "operation_group_id": operation_id,
        },
    )
    if not transition_result.get("ok"):
        return transition_result

    data = dict(transition_result.get("data") or {})
    data["restore_point_created"] = restore_point_created
    data["operation_group_id"] = operation_id
    return {"ok": True, "data": data}

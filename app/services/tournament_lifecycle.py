"""Service layer for tournament lifecycle transitions."""

from __future__ import annotations

from typing import Any

from app.db.repositories import TournamentRepository
from app.domain.tournament_lifecycle import TournamentStatus, can_transition


def transition_tournament_status(
    *,
    connection,
    tournament_id: int,
    to_status: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Change tournament status with UI-friendly structured errors."""

    tournament_repo = TournamentRepository(connection)
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

    return {
        "ok": True,
        "data": {
            "tournament_id": tournament_id,
            "from_status": from_status,
            "to_status": target_status,
        },
    }

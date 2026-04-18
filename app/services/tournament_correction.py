"""Service for controlled tournament corrections."""

from __future__ import annotations

import json
import uuid
from typing import Any

from app.db.repositories import TournamentRepository
from app.domain.tournament_lifecycle import TournamentStatus
from app.services.audit_log import AuditLogService, TOURNAMENT_CORRECTED
from app.services.recalculate_tournament import recalculate_tournament_results
from app.services.tournament_lifecycle import transition_tournament_status

_TOURNAMENT_CORRECTION_FIELDS = (
    "name",
    "date",
    "category_code",
    "league_code",
    "source_files",
    "type",
    "season",
    "series",
    "location",
    "organizer",
    "description",
)


class TournamentCorrectionError(ValueError):
    """Controlled error for tournament correction operation."""


def correct_tournament(
    *,
    connection,
    tournament_id: int,
    reason: str,
    updates: dict[str, Any] | None = None,
    actor: str | None = None,
    operation_group_id: str | None = None,
) -> dict[str, Any]:
    """Apply correction operation for a published tournament.

    The operation requires a reason, writes explicit audit old/new payload,
    recalculates affected results and records correction trace in tournament history.
    """

    normalized_reason = str(reason or "").strip()
    if not normalized_reason:
        raise TournamentCorrectionError("Для коррекции турнира требуется reason.")

    tournament_repo = TournamentRepository(connection)
    audit_log_service = AuditLogService(connection)

    tournament = tournament_repo.get(tournament_id)
    if tournament is None:
        raise TournamentCorrectionError("Турнир не найден.")

    current_status = str(tournament.get("status") or TournamentStatus.DRAFT.value)
    if current_status != TournamentStatus.PUBLISHED.value:
        raise TournamentCorrectionError("Коррекция доступна только для опубликованного турнира.")

    requested_updates = dict(updates or {})
    editable_updates = {
        key: value for key, value in requested_updates.items() if key in _TOURNAMENT_CORRECTION_FIELDS
    }

    old_value = {key: tournament.get(key) for key in _TOURNAMENT_CORRECTION_FIELDS}
    new_value = {**old_value, **editable_updates}

    if editable_updates:
        payload = {**tournament, **editable_updates}
        tournament_repo.update(tournament_id, payload)

    operation_id = operation_group_id or f"corr-{uuid.uuid4()}"
    transition_result = transition_tournament_status(
        connection=connection,
        tournament_id=tournament_id,
        to_status=TournamentStatus.REVIEW.value,
        context={
            "actor": actor or "tournament_correction",
            "reason": normalized_reason,
            "restore": True,
            "audit": {
                "source": "tournament_correction",
                "changed_fields": sorted(editable_updates.keys()),
            },
            "operation_group_id": operation_id,
        },
    )
    if not transition_result.get("ok"):
        error_payload = transition_result.get("error") or {}
        raise TournamentCorrectionError(
            str(error_payload.get("message") or "Не удалось перевести турнир в correction-режим.")
        )

    recalc_report = recalculate_tournament_results(
        connection=connection,
        tournament_id=tournament_id,
    )

    audit_log_service.log_event(
        TOURNAMENT_CORRECTED,
        "Коррекция турнира применена",
        (
            f"Турнир ID: {tournament_id}; изменено полей: {len(editable_updates)}; "
            f"пересчитано результатов: {recalc_report.results_updated}"
        ),
        level="error" if recalc_report.errors else "warning" if recalc_report.warnings else "info",
        context={
            "tournament_id": tournament_id,
            "changed_fields": sorted(editable_updates.keys()),
            "recalculated_results": recalc_report.results_updated,
            "warnings": recalc_report.warnings,
            "errors": recalc_report.errors,
            "history_marker": "correction",
        },
        entity_type="tournament",
        entity_id=str(tournament_id),
        reason=normalized_reason,
        old_value_json=json.dumps(old_value, ensure_ascii=False),
        new_value_json=json.dumps(new_value, ensure_ascii=False),
        source=actor or "tournament_correction",
        operation_group_id=operation_id,
    )

    return {
        "tournament_id": tournament_id,
        "from_status": current_status,
        "to_status": TournamentStatus.REVIEW.value,
        "changed_fields": sorted(editable_updates.keys()),
        "results_recalculated": recalc_report.results_updated,
        "warnings": recalc_report.warnings,
        "errors": recalc_report.errors,
        "operation_group_id": operation_id,
    }

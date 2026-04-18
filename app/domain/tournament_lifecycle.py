"""Tournament lifecycle domain rules."""

from __future__ import annotations

from enum import Enum
from typing import Any


class TournamentStatus(str, Enum):
    """Supported tournament lifecycle statuses."""

    DRAFT = "draft"
    REVIEW = "review"
    CONFIRMED = "confirmed"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    CANCELED = "canceled"


_ALLOWED_TRANSITIONS: dict[TournamentStatus, set[TournamentStatus]] = {
    TournamentStatus.DRAFT: {TournamentStatus.REVIEW, TournamentStatus.CANCELED},
    TournamentStatus.REVIEW: {
        TournamentStatus.DRAFT,
        TournamentStatus.CONFIRMED,
        TournamentStatus.CANCELED,
    },
    TournamentStatus.CONFIRMED: {
        TournamentStatus.PUBLISHED,
        TournamentStatus.ARCHIVED,
        TournamentStatus.REVIEW,
        TournamentStatus.CANCELED,
    },
    TournamentStatus.PUBLISHED: {
        TournamentStatus.ARCHIVED,
        TournamentStatus.REVIEW,
        TournamentStatus.CANCELED,
    },
    TournamentStatus.ARCHIVED: {
        TournamentStatus.REVIEW,
    },
    TournamentStatus.CANCELED: set(),
}

_DANGEROUS_TRANSITIONS: set[tuple[TournamentStatus, TournamentStatus]] = {
    (TournamentStatus.CONFIRMED, TournamentStatus.REVIEW),
    (TournamentStatus.PUBLISHED, TournamentStatus.REVIEW),
    (TournamentStatus.ARCHIVED, TournamentStatus.REVIEW),
}


def _as_status(value: str | TournamentStatus) -> TournamentStatus:
    if isinstance(value, TournamentStatus):
        return value
    return TournamentStatus(str(value).strip().lower())


def allowed_targets(status: str | TournamentStatus) -> set[str]:
    """Return allowed transition targets for a source status."""

    source = _as_status(status)
    return {item.value for item in _ALLOWED_TRANSITIONS[source]}


def can_transition(
    from_status: str | TournamentStatus,
    to_status: str | TournamentStatus,
    context: dict[str, Any] | None = None,
) -> bool:
    """Validate lifecycle transition.

    Dangerous rollback-like transitions require control metadata in context:
    - reason: non-empty text
    - restore: True
    - audit: truthy object (usually actor/ticket payload)
    """

    source = _as_status(from_status)
    target = _as_status(to_status)
    if source == target:
        return True

    allowed = _ALLOWED_TRANSITIONS.get(source, set())
    if target not in allowed:
        return False

    if (source, target) not in _DANGEROUS_TRANSITIONS:
        return True

    payload = context or {}
    reason = str(payload.get("reason") or "").strip()
    restore = payload.get("restore") is True
    audit = payload.get("audit")
    return bool(reason) and restore and bool(audit)

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from app.db.repositories import RatingSnapshotRepository, ResultRepository, TournamentRepository
from app.domain.rating import RatingBasisItem, build_rating_basis, build_rating_snapshot
from app.services.audit_log import AuditLogService, RATING_SNAPSHOT_CREATED

CATEGORY_SCOPE = "category"
LEAGUE_SCOPE = "league"
ADULT_SCOPE = "adult"
ADULT_OVERALL_SCOPE_KEY = "overall"
ADULT_MEN_SCOPE_KEY = "men"
ADULT_WOMEN_SCOPE_KEY = "women"
SNAPSHOT_REASON_PUBLISH = "publish"


@dataclass(frozen=True)
class RatingSnapshotEntry:
    id: int
    scope_type: str
    scope_key: str
    player_id: int
    position: int
    fio: str
    points: int
    tournaments_count: int
    rolling_basis: list[RatingBasisItem]
    source_tournament_id: int
    reason: str
    operation_group_id: str | None
    created_at: str


@dataclass(frozen=True)
class RatingSnapshotSession:
    scope_type: str
    scope_key: str
    source_tournament_id: int
    reason: str
    operation_group_id: str | None
    created_at: str
    entries_count: int


@dataclass(frozen=True)
class SnapshotCreateResult:
    created: bool
    reason: str | None
    session: RatingSnapshotSession | None
    entries_created: int = 0
    sessions: tuple[RatingSnapshotSession, ...] = ()


@dataclass(frozen=True)
class PlayerRatingStateEntry:
    scope_type: str
    scope_key: str
    player_id: int
    fio: str
    position: int
    points: int
    tournaments_count: int
    source_tournament_id: int
    created_at: str


def create_rating_snapshot_for_tournament_publish(
    connection,
    tournament_id: int,
    n_value: int = 6,
    operation_group_id: str | None = None,
) -> SnapshotCreateResult:
    tournament_repo = TournamentRepository(connection)
    result_repo = ResultRepository(connection)
    snapshot_repo = RatingSnapshotRepository(connection)
    audit_log_service = AuditLogService(connection)

    tournament = tournament_repo.get(tournament_id)
    if tournament is None:
        return SnapshotCreateResult(created=False, reason="Tournament not found.", session=None)

    scope_requests = _build_scope_requests(tournament)
    if not scope_requests:
        return SnapshotCreateResult(
            created=False,
            reason="Tournament category, league, or adult mode is required for snapshot creation.",
            session=None,
        )
    created_at = datetime.now(timezone.utc).isoformat(timespec="microseconds")
    reason = SNAPSHOT_REASON_PUBLISH
    created_sessions: list[RatingSnapshotSession] = []
    created_count = 0
    for scope_type, scope_key, filters in scope_requests:
        published_results = result_repo.list_results_for_rating(**filters)
        if not published_results:
            continue

        snapshot_rows = build_rating_snapshot(published_results, n_value)
        if not snapshot_rows:
            continue

        basis_by_player = build_rating_basis(published_results, n_value)
        payload_rows = [
            {
                "scope_type": scope_type,
                "scope_key": scope_key,
                "player_id": row.player_id,
                "position": row.place,
                "points": row.points,
                "tournaments_count": row.tournaments_count,
                "rolling_basis_json": json.dumps(
                    [asdict(item) for item in basis_by_player.get(row.player_id, [])],
                    ensure_ascii=False,
                ),
                "source_tournament_id": tournament_id,
                "reason": reason,
                "operation_group_id": operation_group_id,
                "created_at": created_at,
            }
            for row in snapshot_rows
        ]
        scope_count = snapshot_repo.create_many(payload_rows)
        created_count += scope_count
        session = RatingSnapshotSession(
            scope_type=scope_type,
            scope_key=scope_key,
            source_tournament_id=tournament_id,
            reason=reason,
            operation_group_id=operation_group_id,
            created_at=created_at,
            entries_count=scope_count,
        )
        created_sessions.append(session)
        audit_log_service.log_event(
            RATING_SNAPSHOT_CREATED,
            "Rating snapshot created",
            (
                f"Tournament ID: {tournament_id}; "
                f"scope={scope_type}:{scope_key}; "
                f"entries={scope_count}"
            ),
            context={
                "scope_type": scope_type,
                "scope_key": scope_key,
                "source_tournament_id": tournament_id,
                "reason": reason,
                "created_at": created_at,
                "entries_count": scope_count,
            },
            entity_type="tournament",
            entity_id=str(tournament_id),
            source="rating_snapshot",
            operation_group_id=operation_group_id,
        )

    if not created_sessions:
        return SnapshotCreateResult(
            created=False,
            reason="Нет опубликованных результатов для поддерживаемых разделов рейтинга.",
            session=None,
        )

    return SnapshotCreateResult(
        created=True,
        reason=None,
        session=created_sessions[0],
        entries_created=created_count,
        sessions=tuple(created_sessions),
    )


def list_rating_snapshot_sessions(
    connection,
    scope_type: str,
    scope_key: str,
) -> list[RatingSnapshotSession]:
    snapshot_repo = RatingSnapshotRepository(connection)
    return [
        RatingSnapshotSession(
            scope_type=str(row["scope_type"]),
            scope_key=str(row["scope_key"]),
            source_tournament_id=int(row["source_tournament_id"]),
            reason=str(row["reason"]),
            operation_group_id=str(row["operation_group_id"]) if row["operation_group_id"] is not None else None,
            created_at=str(row["created_at"]),
            entries_count=int(row["entries_count"]),
        )
        for row in snapshot_repo.list_sessions(scope_type=scope_type, scope_key=scope_key)
    ]


def list_rating_snapshot_rows(
    connection,
    *,
    snapshot_created_at: str,
    scope_type: str,
    scope_key: str,
) -> list[RatingSnapshotEntry]:
    snapshot_repo = RatingSnapshotRepository(connection)
    rows = snapshot_repo.list_rows(
        snapshot_created_at=snapshot_created_at,
        scope_type=scope_type,
        scope_key=scope_key,
    )
    return [_snapshot_entry_from_row(row) for row in rows]


def list_latest_player_rating_states(connection, *, player_id: int) -> list[PlayerRatingStateEntry]:
    snapshot_repo = RatingSnapshotRepository(connection)
    rows = snapshot_repo.list_latest_rows_for_player(player_id)
    return [
        PlayerRatingStateEntry(
            scope_type=str(row["scope_type"]),
            scope_key=str(row["scope_key"]),
            player_id=int(row["player_id"]),
            fio=_build_fio(row),
            position=int(row["position"]),
            points=int(row["points"]),
            tournaments_count=int(row["tournaments_count"]),
            source_tournament_id=int(row["source_tournament_id"]),
            created_at=str(row["created_at"]),
        )
        for row in rows
    ]


def _snapshot_entry_from_row(row: dict[str, object]) -> RatingSnapshotEntry:
    return RatingSnapshotEntry(
        id=int(row["id"]),
        scope_type=str(row["scope_type"]),
        scope_key=str(row["scope_key"]),
        player_id=int(row["player_id"]),
        position=int(row["position"]),
        fio=_build_fio(row),
        points=int(row["points"]),
        tournaments_count=int(row["tournaments_count"]),
        rolling_basis=_parse_basis_json(row.get("rolling_basis_json")),
        source_tournament_id=int(row["source_tournament_id"]),
        reason=str(row["reason"]),
        operation_group_id=str(row["operation_group_id"]) if row["operation_group_id"] is not None else None,
        created_at=str(row["created_at"]),
    )


def _parse_basis_json(raw_value: object) -> list[RatingBasisItem]:
    try:
        payload = json.loads(str(raw_value or "[]"))
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    basis_items: list[RatingBasisItem] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        basis_items.append(
            RatingBasisItem(
                tournament_id=int(item.get("tournament_id") or 0),
                tournament_date=str(item.get("tournament_date") or ""),
                points_total=int(item.get("points_total") or 0),
            )
        )
    return basis_items


def _build_fio(row: dict[str, object]) -> str:
    last_name = str(row.get("last_name") or "").strip()
    first_name = str(row.get("first_name") or "").strip()
    middle_name = str(row.get("middle_name") or "").strip()
    return " ".join(part for part in (last_name, first_name, middle_name) if part)


def _build_scope_requests(
    tournament: dict[str, object],
) -> list[tuple[str, str, dict[str, object]]]:
    requests: list[tuple[str, str, dict[str, object]]] = []
    is_adult_mode = bool(int(tournament.get("is_adult_mode") or 0))
    category_code = str(tournament.get("category_code") or "").strip()
    if category_code and not is_adult_mode:
        requests.append(
            (
                CATEGORY_SCOPE,
                category_code,
                {"category_code": category_code},
            )
        )

    league_code = str(tournament.get("league_code") or "").strip()
    if league_code:
        requests.append(
            (
                LEAGUE_SCOPE,
                league_code,
                {"league_code": league_code},
            )
        )
    if is_adult_mode:
        requests.append(
            (
                ADULT_SCOPE,
                ADULT_OVERALL_SCOPE_KEY,
                {"is_adult_mode": True},
            )
        )
        requests.append(
            (
                ADULT_SCOPE,
                ADULT_MEN_SCOPE_KEY,
                {"is_adult_mode": True, "adult_gender_scope": ADULT_MEN_SCOPE_KEY},
            )
        )
        requests.append(
            (
                ADULT_SCOPE,
                ADULT_WOMEN_SCOPE_KEY,
                {"is_adult_mode": True, "adult_gender_scope": ADULT_WOMEN_SCOPE_KEY},
            )
        )
    return requests

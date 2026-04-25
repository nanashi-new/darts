from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.db.repositories import LeagueTransferRepository, ResultRepository, TournamentRepository
from app.services.audit_log import AuditLogService, LEAGUE_TRANSFER_CREATED

TRANSFER_REASON_PUBLISH = "publish"


@dataclass(frozen=True)
class LeagueTransferPreviewRow:
    player_id: int
    fio: str
    from_league_code: str | None
    to_league_code: str


@dataclass(frozen=True)
class LeagueTransferPreview:
    available: bool
    reason: str | None
    rows: list[LeagueTransferPreviewRow]


@dataclass(frozen=True)
class LeagueTransferEvent:
    id: int
    player_id: int
    fio: str
    from_league_code: str | None
    to_league_code: str
    source_tournament_id: int
    tournament_name: str
    tournament_date: str
    reason: str
    operation_group_id: str | None
    created_at: str


@dataclass(frozen=True)
class TransferRecordResult:
    recorded_count: int
    rows: tuple[LeagueTransferPreviewRow, ...]


def build_league_transfer_preview(*, connection, tournament_id: int) -> LeagueTransferPreview:
    tournament_repo = TournamentRepository(connection)
    result_repo = ResultRepository(connection)
    transfer_repo = LeagueTransferRepository(connection)

    tournament = tournament_repo.get(tournament_id)
    if tournament is None:
        return LeagueTransferPreview(available=False, reason="Турнир не найден.", rows=[])

    league_code = str(tournament.get("league_code") or "").strip()
    if not league_code:
        return LeagueTransferPreview(
            available=False,
            reason="Предпросмотр переходов между лигами недоступен: не указана лига.",
            rows=[],
        )

    current_rows = result_repo.list_with_players(tournament_id)
    if not current_rows:
        return LeagueTransferPreview(
            available=False,
            reason="Предпросмотр переходов между лигами недоступен: в турнире пока нет результатов.",
            rows=[],
        )

    seen_player_ids: set[int] = set()
    preview_rows: list[LeagueTransferPreviewRow] = []
    for row in current_rows:
        player_id = int(row["player_id"])
        if player_id in seen_player_ids:
            continue
        seen_player_ids.add(player_id)
        latest_event = transfer_repo.get_latest_for_player(player_id)
        from_league_code = (
            str(latest_event.get("to_league_code")) if latest_event and latest_event.get("to_league_code") is not None else None
        )
        if from_league_code == league_code:
            continue
        preview_rows.append(
            LeagueTransferPreviewRow(
                player_id=player_id,
                fio=_build_fio(row),
                from_league_code=from_league_code,
                to_league_code=league_code,
            )
        )

    preview_rows.sort(key=lambda row: row.fio)
    return LeagueTransferPreview(available=True, reason=None, rows=preview_rows)


def record_league_transfers_for_tournament_publish(
    *,
    connection,
    tournament_id: int,
    operation_group_id: str | None = None,
) -> TransferRecordResult:
    preview = build_league_transfer_preview(connection=connection, tournament_id=tournament_id)
    if not preview.available or not preview.rows:
        return TransferRecordResult(recorded_count=0, rows=())

    transfer_repo = LeagueTransferRepository(connection)
    audit_log_service = AuditLogService(connection)
    created_at = datetime.now(timezone.utc).isoformat(timespec="microseconds")
    entries = [
        {
            "player_id": row.player_id,
            "from_league_code": row.from_league_code,
            "to_league_code": row.to_league_code,
            "source_tournament_id": tournament_id,
            "reason": TRANSFER_REASON_PUBLISH,
            "operation_group_id": operation_group_id,
            "created_at": created_at,
        }
        for row in preview.rows
    ]
    transfer_repo.create_many(entries)
    for row in preview.rows:
        audit_log_service.log_event(
            LEAGUE_TRANSFER_CREATED,
            "Создан переход между лигами",
            (
                f"Игрок ID: {row.player_id}; "
                f"{row.from_league_code or '-'} -> {row.to_league_code}; "
                f"турнир_id={tournament_id}"
            ),
            context={
                "player_id": row.player_id,
                "from_league_code": row.from_league_code,
                "to_league_code": row.to_league_code,
                "source_tournament_id": tournament_id,
                "operation_group_id": operation_group_id,
            },
            entity_type="tournament",
            entity_id=str(tournament_id),
            source="league_transfer",
            operation_group_id=operation_group_id,
        )
    return TransferRecordResult(recorded_count=len(preview.rows), rows=tuple(preview.rows))


def list_player_league_transfers(connection, player_id: int) -> list[LeagueTransferEvent]:
    repo = LeagueTransferRepository(connection)
    return [
        LeagueTransferEvent(
            id=int(row["id"]),
            player_id=int(row["player_id"]),
            fio=_build_fio(row),
            from_league_code=str(row["from_league_code"]) if row["from_league_code"] is not None else None,
            to_league_code=str(row["to_league_code"]),
            source_tournament_id=int(row["source_tournament_id"]),
            tournament_name=str(row.get("tournament_name") or ""),
            tournament_date=str(row.get("tournament_date") or ""),
            reason=str(row["reason"]),
            operation_group_id=str(row["operation_group_id"]) if row["operation_group_id"] is not None else None,
            created_at=str(row["created_at"]),
        )
        for row in repo.list_for_player(player_id)
    ]


def _build_fio(row: dict[str, object]) -> str:
    last_name = str(row.get("last_name") or "").strip()
    first_name = str(row.get("first_name") or "").strip()
    middle_name = str(row.get("middle_name") or "").strip()
    return " ".join(part for part in (last_name, first_name, middle_name) if part)

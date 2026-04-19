from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from uuid import uuid4

from app.db.repositories import PlayerRepository, ResultRepository, TournamentRepository
from app.services.audit_log import AuditLogService, TOURNAMENT_CREATED


@dataclass(frozen=True)
class ManualTournamentCreateReport:
    tournament_id: int
    tournament_name: str
    tournament_status: str
    imported_rows: int
    skipped_rows: int
    warnings: list[str]
    operation_group_id: str


def create_manual_adult_tournament(
    *,
    connection,
    tournament_name: str,
    tournament_date: str | None,
    league_code: str | None,
    rows: Iterable[dict[str, object]],
    operation_group_id: str | None = None,
) -> ManualTournamentCreateReport:
    normalized_name = str(tournament_name or "").strip()
    if not normalized_name:
        raise ValueError("Tournament name is required.")

    tournament_repo = TournamentRepository(connection)
    player_repo = PlayerRepository(connection)
    result_repo = ResultRepository(connection)
    audit_log = AuditLogService(connection)

    normalized_league = str(league_code or "").strip() or None
    operation_group_id_value = str(operation_group_id or "").strip() or uuid4().hex
    tournament_id = tournament_repo.create(
        {
            "name": normalized_name,
            "date": tournament_date,
            "category_code": None,
            "league_code": normalized_league,
            "is_adult_mode": 1,
            "source_files": "[]",
            "status": "draft",
            "has_draft_changes": 1,
        }
    )

    warnings: list[str] = []
    imported_rows = 0
    skipped_rows = 0

    for index, row in enumerate(rows, start=1):
        fio = str(row.get("fio") or "").strip()
        if not fio:
            warnings.append(f"Row {index}: missing FIO.")
            skipped_rows += 1
            continue

        last_name, first_name, middle_name = _parse_fio(fio)
        if not last_name or not first_name:
            warnings.append(f"Row {index}: incomplete FIO '{fio}'.")
            skipped_rows += 1
            continue

        birth_date, birth_year = _parse_birth_value(row.get("birth"))
        place = _parse_int(row.get("place"))
        points_total = _parse_int(row.get("points_total"))
        if points_total is None:
            warnings.append(f"Row {index}: points_total is required for adult manual flow.")
            skipped_rows += 1
            continue

        player = player_repo.find_by_identity(
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
            birth_date=birth_date,
            birth_year=birth_year,
        )
        if player is None:
            player_id = player_repo.create(
                {
                    "last_name": last_name,
                    "first_name": first_name,
                    "middle_name": middle_name,
                    "birth_date": birth_date,
                    "gender": None,
                    "coach": None,
                    "club": None,
                    "notes": None,
                }
            )
        else:
            player_id = int(player["id"])

        result_repo.create(
            {
                "tournament_id": tournament_id,
                "player_id": player_id,
                "place": place,
                "score_set": None,
                "score_sector20": None,
                "score_big_round": None,
                "rank_set": None,
                "rank_sector20": None,
                "rank_big_round": None,
                "points_classification": 0,
                "points_place": points_total,
                "points_total": points_total,
                "calc_version": "manual_adult_v1",
            }
        )
        imported_rows += 1

    if imported_rows == 0:
        raise ValueError("Adult manual tournament requires at least one valid result row.")

    audit_log.log_event(
        TOURNAMENT_CREATED,
        "Manual adult tournament created",
        (
            f"Tournament ID: {tournament_id}; rows={imported_rows}; "
            f"skipped={skipped_rows}"
        ),
        context={
            "tournament_id": tournament_id,
            "is_adult_mode": True,
            "league_code": normalized_league,
            "imported_rows": imported_rows,
            "skipped_rows": skipped_rows,
            "warnings": warnings,
        },
        entity_type="tournament",
        entity_id=str(tournament_id),
        source="manual_tournament",
        operation_group_id=operation_group_id_value,
    )

    return ManualTournamentCreateReport(
        tournament_id=tournament_id,
        tournament_name=normalized_name,
        tournament_status="draft",
        imported_rows=imported_rows,
        skipped_rows=skipped_rows,
        warnings=warnings,
        operation_group_id=operation_group_id_value,
    )


def _parse_fio(value: str) -> tuple[str, str, str | None]:
    parts = [part.strip() for part in str(value).split() if part.strip()]
    if not parts:
        return "", "", None
    last_name = parts[0]
    first_name = parts[1] if len(parts) > 1 else ""
    middle_name = " ".join(parts[2:]) if len(parts) > 2 else None
    return last_name, first_name, middle_name


def _parse_birth_value(value: object | None) -> tuple[str | None, str | None]:
    if value is None:
        return None, None
    text = str(value).strip()
    if not text:
        return None, None
    if len(text) == 4 and text.isdigit():
        return None, text
    return text, text[:4] if len(text) >= 4 and text[:4].isdigit() else None


def _parse_int(value: object | None) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(float(text.replace(",", ".")))
    except (TypeError, ValueError):
        return None

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Callable, Iterable

from app.db.repositories import PlayerRepository
from app.services.import_xlsx import (
    ImportApplyReport,
    PlayerMatchResolution,
    TableBlock,
    _normalize_text,
    _parse_birth_value,
    _parse_fio,
    find_player_candidates,
    import_tournament_rows,
    import_tournament_table_blocks,
)


@dataclass(frozen=True)
class PlayersImportReport:
    created: int
    existing: int
    details: list[str]


@dataclass(frozen=True)
class UpdatePlayersReport:
    created: int
    updated: int
    unchanged: int
    details: list[str]


def import_full(
    *,
    connection: sqlite3.Connection,
    blocks: list[TableBlock],
    tournament_name: str,
    tournament_date: str,
    category_code: str | None,
    is_adult_mode: bool,
    source_files: list[str],
    player_match_resolver: Callable[
        [str, str | None, list[dict[str, object]]], PlayerMatchResolution | None
    ]
    | None = None,
    operation_group_id: str | None = None,
) -> ImportApplyReport:
    """Mode 1: Full import - delegates to import_tournament_table_blocks."""
    return import_tournament_table_blocks(
        connection=connection,
        blocks=blocks,
        tournament_name=tournament_name,
        tournament_date=tournament_date,
        category_code=category_code,
        is_adult_mode=is_adult_mode,
        source_files=source_files,
        player_match_resolver=player_match_resolver,
        operation_group_id=operation_group_id,
    )


def import_players_only(
    *,
    connection: sqlite3.Connection,
    blocks: list[TableBlock],
) -> PlayersImportReport:
    """Mode 2: Import only players (create new, skip existing)."""
    player_repo = PlayerRepository(connection)
    created = 0
    existing = 0
    details: list[str] = []

    for block in blocks:
        for row in block.rows:
            fio = row.get("fio")
            if fio is None or _normalize_text(fio) == "":
                continue

            last_name, first_name, middle_name = _parse_fio(fio)
            birth_date, birth_year = _parse_birth_value(row.get("birth"))

            candidates = find_player_candidates(
                fio=fio,
                birth_date_or_year=birth_date or birth_year,
                player_repo=player_repo,
            )

            if candidates:
                existing += 1
            else:
                coach_raw = row.get("coach")
                coach = _normalize_text(coach_raw) if coach_raw is not None else None
                player_repo.create(
                    {
                        "last_name": last_name,
                        "first_name": first_name,
                        "middle_name": middle_name,
                        "birth_date": birth_date or birth_year,
                        "gender": None,
                        "coach": coach if coach else None,
                        "club": None,
                        "notes": None,
                    }
                )
                created += 1
                details.append(f"Создан: {last_name} {first_name}")

    return PlayersImportReport(created=created, existing=existing, details=details)


def import_update_players(
    *,
    connection: sqlite3.Connection,
    blocks: list[TableBlock],
) -> UpdatePlayersReport:
    """Mode 3: Update existing players (fill empty coach/birth) or create new."""
    player_repo = PlayerRepository(connection)
    created = 0
    updated = 0
    unchanged = 0
    details: list[str] = []

    for block in blocks:
        for row in block.rows:
            fio = row.get("fio")
            if fio is None or _normalize_text(fio) == "":
                continue

            last_name, first_name, middle_name = _parse_fio(fio)
            birth_date, birth_year = _parse_birth_value(row.get("birth"))

            candidates = find_player_candidates(
                fio=fio,
                birth_date_or_year=birth_date or birth_year,
                player_repo=player_repo,
            )

            if not candidates:
                coach_raw = row.get("coach")
                coach = _normalize_text(coach_raw) if coach_raw is not None else None
                player_repo.create(
                    {
                        "last_name": last_name,
                        "first_name": first_name,
                        "middle_name": middle_name,
                        "birth_date": birth_date or birth_year,
                        "gender": None,
                        "coach": coach if coach else None,
                        "club": None,
                        "notes": None,
                    }
                )
                created += 1
                details.append(f"Создан: {last_name} {first_name}")
            else:
                player = candidates[0]
                player_id = int(player["id"])  # type: ignore[call-overload]
                needs_update = False

                player_coach = _normalize_text(player.get("coach"))
                coach_raw = row.get("coach")
                row_coach = _normalize_text(coach_raw) if coach_raw is not None else ""

                player_birth = _normalize_text(player.get("birth_date"))

                new_coach = player_coach
                new_birth = player_birth

                if not player_coach and row_coach:
                    new_coach = row_coach
                    needs_update = True

                if not player_birth and (birth_date or birth_year):
                    new_birth = birth_date or birth_year or ""
                    needs_update = True

                if needs_update:
                    player_repo.update(
                        player_id,
                        {
                            "last_name": player.get("last_name"),
                            "first_name": player.get("first_name"),
                            "middle_name": player.get("middle_name"),
                            "birth_date": new_birth if new_birth else player.get("birth_date"),
                            "gender": player.get("gender"),
                            "coach": new_coach if new_coach else player.get("coach"),
                            "club": player.get("club"),
                            "notes": player.get("notes"),
                        },
                    )
                    updated += 1
                    details.append(f"Обновлен: {last_name} {first_name}")
                else:
                    unchanged += 1

    return UpdatePlayersReport(
        created=created,
        updated=updated,
        unchanged=unchanged,
        details=details,
    )


def import_multi_tournament(
    *,
    connection: sqlite3.Connection,
    blocks: list[TableBlock],
    base_name: str,
    tournament_date: str,
    is_adult_mode: bool,
    source_files: list[str],
    player_match_resolver: Callable[
        [str, str | None, list[dict[str, object]]], PlayerMatchResolution | None
    ]
    | None = None,
    operation_group_id: str | None = None,
) -> list[ImportApplyReport]:
    """Mode 4: Multi-tournament - each block becomes a separate tournament."""
    reports: list[ImportApplyReport] = []
    for block in blocks:
        tournament_name = f"{base_name} - {block.sheet_name}"
        report = import_tournament_rows(
            connection=connection,
            rows=block.rows,
            tournament_name=tournament_name,
            tournament_date=tournament_date,
            category_code=None,
            is_adult_mode=is_adult_mode,
            source_files=source_files,
            player_match_resolver=player_match_resolver,
            operation_group_id=operation_group_id,
        )
        reports.append(report)
    return reports

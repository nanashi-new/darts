from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from app.db.repositories import PlayerRepository
from app.services.audit_log import AuditLogService
from app.services.import_xlsx import _normalize_fio_key

MERGE_PLAYERS = "MERGE_PLAYERS"


@dataclass(frozen=True)
class DuplicateGroup:
    normalized_fio: str
    players: list[dict[str, object]]


@dataclass(frozen=True)
class MergeResult:
    primary_id: int
    duplicate_id: int
    results_transferred: int
    duplicate_results_removed: int



def normalize_fio(fio: object) -> str:
    return _normalize_fio_key(fio)


class PlayerMergeService:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._player_repo = PlayerRepository(connection)
        self._audit_log = AuditLogService(connection)


    def count_results_for_player(self, player_id: int) -> int:
        row = self._connection.execute(
            "SELECT COUNT(*) FROM results WHERE player_id = ?",
            (player_id,),
        ).fetchone()
        return int(row[0]) if row else 0

    def find_possible_duplicates(self) -> list[DuplicateGroup]:
        grouped: dict[str, list[dict[str, object]]] = {}
        for player in self._player_repo.list():
            fio = " ".join(
                part
                for part in (
                    player.get("last_name"),
                    player.get("first_name"),
                    player.get("middle_name"),
                )
                if part
            )
            normalized = normalize_fio(fio)
            if not normalized:
                continue
            grouped.setdefault(normalized, []).append(player)

        duplicates = [
            DuplicateGroup(normalized_fio=normalized, players=players)
            for normalized, players in grouped.items()
            if len(players) > 1
        ]
        duplicates.sort(key=lambda item: item.normalized_fio)
        return duplicates

    def merge_players(self, primary_id: int, duplicate_id: int, merge_strategy: str = "prefer_primary") -> MergeResult:
        if primary_id == duplicate_id:
            raise ValueError("Нельзя объединить игрока с самим собой.")

        primary = self._player_repo.get(primary_id)
        duplicate = self._player_repo.get(duplicate_id)
        if primary is None:
            raise ValueError("Основной игрок не найден.")
        if duplicate is None:
            raise ValueError("Дублирующий игрок не найден.")

        duplicate_results = self._connection.execute(
            "SELECT * FROM results WHERE player_id = ? ORDER BY id",
            (duplicate_id,),
        ).fetchall()

        transferred = 0
        removed = 0

        with self._connection:
            for row in duplicate_results:
                existing = self._connection.execute(
                    "SELECT id, points_total FROM results WHERE tournament_id = ? AND player_id = ?",
                    (row["tournament_id"], primary_id),
                ).fetchone()
                if existing is None:
                    self._connection.execute(
                        "UPDATE results SET player_id = ? WHERE id = ?",
                        (primary_id, row["id"]),
                    )
                    transferred += 1
                    continue

                keep_duplicate = merge_strategy == "prefer_duplicate" and (
                    row["points_total"] or 0
                ) > (existing["points_total"] or 0)
                if keep_duplicate:
                    self._connection.execute(
                        "UPDATE results SET player_id = ? WHERE id = ?",
                        (primary_id, row["id"]),
                    )
                    self._connection.execute("DELETE FROM results WHERE id = ?", (existing["id"],))
                    transferred += 1
                else:
                    self._connection.execute("DELETE FROM results WHERE id = ?", (row["id"],))
                    removed += 1

            patch = {
                "last_name": primary.get("last_name"),
                "first_name": primary.get("first_name"),
                "middle_name": primary.get("middle_name"),
                "birth_date": primary.get("birth_date"),
                "gender": primary.get("gender"),
                "coach": primary.get("coach") or duplicate.get("coach"),
                "club": primary.get("club") or duplicate.get("club"),
                "notes": primary.get("notes") or duplicate.get("notes"),
            }
            self._player_repo.update(primary_id, patch)
            self._player_repo.delete(duplicate_id)

        self._audit_log.log_event(
            MERGE_PLAYERS,
            "Слияние дублей игроков",
            f"Слили игрока #{duplicate_id} в #{primary_id}. Перенесено результатов: {transferred}. Удалено дублей результатов: {removed}.",
            context={
                "primary_id": primary_id,
                "duplicate_id": duplicate_id,
                "merge_strategy": merge_strategy,
                "results_transferred": transferred,
                "duplicate_results_removed": removed,
            },
        )

        return MergeResult(
            primary_id=primary_id,
            duplicate_id=duplicate_id,
            results_transferred=transferred,
            duplicate_results_removed=removed,
        )

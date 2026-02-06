from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
import sqlite3

from app.db.repositories import ResultRepository, TournamentRepository
from app.services.export_service import ExportService


@dataclass
class BatchExportResult:
    run_directory: Path
    files_created: list[Path]


class BatchExportService:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._tournament_repo = TournamentRepository(connection)
        self._result_repo = ResultRepository(connection)
        self._export_service = ExportService()

    def export_all(self, base_directory: str | Path, export_format: str, n_value: int = 6) -> BatchExportResult:
        run_directory = Path(base_directory) / "exports" / f"{date.today().isoformat()}_run"
        ratings_dir = run_directory / "ratings"
        tournaments_dir = run_directory / "tournaments"
        ratings_dir.mkdir(parents=True, exist_ok=True)
        tournaments_dir.mkdir(parents=True, exist_ok=True)

        files_created: list[Path] = []
        for category in self._tournament_repo.list_category_codes():
            rows = self._build_rating_rows(category, n_value)
            extension = self._normalize_extension(export_format)
            target_path = ratings_dir / f"rating_{self._slug(category)}.{extension}"
            self._export_service.export_dataset(
                export_format=export_format,
                path=str(target_path),
                header_lines=[
                    "Рейтинг",
                    f"Дата: {self._export_service.format_date_label()}",
                    f"Категория: {category}",
                    f"N: {n_value}",
                ],
                columns=["Место", "ФИО", "Очки", "Учтено турниров"],
                rows=rows,
            )
            files_created.append(target_path)

        for tournament in self._tournament_repo.list():
            tournament_id = int(tournament["id"])
            rows = self._build_protocol_rows(tournament_id)
            name = tournament.get("name") or f"tournament_{tournament_id}"
            extension = self._normalize_extension(export_format)
            target_path = tournaments_dir / f"protocol_{self._slug(str(name))}_{tournament_id}.{extension}"
            self._export_service.export_dataset(
                export_format=export_format,
                path=str(target_path),
                header_lines=[
                    "Протокол турнира",
                    f"Дата: {tournament.get('date') or 'дата не указана'}",
                    f"Категория: {tournament.get('category_code') or 'категория не указана'}",
                    f"N: {n_value}",
                ],
                columns=[
                    "Место",
                    "ФИО",
                    "Дата рождения",
                    "Набор очков",
                    "Сектор 20",
                    "Большой раунд",
                    "Очки за место",
                    "Очки классификации",
                    "Итого",
                ],
                rows=rows,
            )
            files_created.append(target_path)

        return BatchExportResult(run_directory=run_directory, files_created=files_created)

    def _build_rating_rows(self, category_code: str, n_value: int) -> list[list[str]]:
        results = self._result_repo.list_results_for_rating(category_code=category_code)
        players: dict[int, dict[str, object]] = {}
        for entry in results:
            player_id = int(entry["player_id"])
            players.setdefault(player_id, {"entries": [], "fio": ""})
            players[player_id]["entries"].append(entry)
            fio = " ".join(
                part
                for part in [
                    str(entry.get("last_name") or ""),
                    str(entry.get("first_name") or ""),
                    str(entry.get("middle_name") or ""),
                ]
                if part
            )
            players[player_id]["fio"] = fio

        rating_rows: list[dict[str, object]] = []
        for player in players.values():
            entries = player["entries"]
            points_list = [int(entry.get("points_total") or 0) for entry in entries]
            rating_rows.append(
                {
                    "fio": str(player["fio"]),
                    "points": sum(points_list[:n_value]),
                    "tournaments_count": min(len(points_list), n_value),
                }
            )

        rating_rows.sort(key=lambda row: (-int(row["points"]), str(row["fio"])))
        return [
            [str(index), str(row["fio"]), str(row["points"]), str(row["tournaments_count"])]
            for index, row in enumerate(rating_rows, start=1)
        ]

    def _build_protocol_rows(self, tournament_id: int) -> list[list[str]]:
        results = self._result_repo.list_with_players(tournament_id)
        rows: list[list[str]] = []
        for result in results:
            fio = " ".join(
                part
                for part in [
                    str(result.get("last_name") or ""),
                    str(result.get("first_name") or ""),
                    str(result.get("middle_name") or ""),
                ]
                if part
            )
            rows.append(
                [
                    str(result.get("place") or ""),
                    fio,
                    str(result.get("birth_date") or ""),
                    str(result.get("score_set") or ""),
                    str(result.get("score_sector20") or ""),
                    str(result.get("score_big_round") or ""),
                    str(result.get("points_place") or ""),
                    str(result.get("points_classification") or ""),
                    str(result.get("points_total") or ""),
                ]
            )
        return rows

    @staticmethod
    def _slug(value: str) -> str:
        normalized = re.sub(r"[^\w\-]+", "_", value.strip().lower())
        return normalized.strip("_") or "item"

    @staticmethod
    def _normalize_extension(export_format: str) -> str:
        lowered = export_format.lower()
        if lowered == "jpeg":
            return "jpg"
        return lowered

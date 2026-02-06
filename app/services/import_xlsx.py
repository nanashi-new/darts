from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import json
from typing import Iterable

from openpyxl import load_workbook

from app.db.repositories import PlayerRepository, ResultRepository, TournamentRepository
from app.domain.points import points_for_place
from app.domain.ranks import calculate_points_classification
from app.services.norms_loader import load_norms_from_settings


@dataclass(frozen=True)
class ParsedTable:
    headers: list[str]
    rows: list[dict[str, object]]


@dataclass(frozen=True)
class ImportParseReport:
    headers: list[str]
    rows: list[dict[str, object]]
    errors: list[str]
    warnings: list[str]
    needs_mapping: bool
    confidence: float


def _normalize_header(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    return "".join(ch for ch in text if ch.isalnum())


def detect_headers(row_values: Iterable[object]) -> dict[str, int]:
    synonyms = {
        "fio": ["фио", "игрок", "фамилияимя", "фамилия", "имя"],
        "birth": ["др", "датарождения", "годрождения", "рождения"],
        "coach": ["тренер", "coach"],
        "place": ["место", "place"],
        "score_set": ["набор", "очки", "наборочков", "score"],
        "score_sector20": ["с20", "sector20", "сектор20"],
        "score_big_round": ["бр", "biground", "большойраунд"],
    }
    normalized_synonyms = {
        key: {_normalize_header(item) for item in values}
        for key, values in synonyms.items()
    }

    mapping: dict[str, int] = {}
    for idx, cell_value in enumerate(row_values):
        normalized = _normalize_header(cell_value)
        if not normalized:
            continue
        for key, options in normalized_synonyms.items():
            if normalized in options:
                mapping[key] = idx
                break
    return mapping


def _is_row_empty(row_values: Iterable[object]) -> bool:
    for value in row_values:
        if value is None:
            continue
        if str(value).strip() != "":
            return False
    return True


def _row_has_total(row_values: Iterable[object]) -> bool:
    for value in row_values:
        if value is None:
            continue
        if "итого" in str(value).strip().lower():
            return True
    return False


def _parse_first_table(path: str) -> tuple[
    list[str],
    list[dict[str, object]],
    dict[str, int],
    bool,
]:
    workbook = load_workbook(path, data_only=True)
    sheet = workbook.active

    header_mapping: dict[str, int] = {}
    header_labels: list[str] = []
    rows: list[dict[str, object]] = []
    header_found = False

    for row in sheet.iter_rows(values_only=True):
        row_values = list(row)
        if not header_found:
            candidate_mapping = detect_headers(row_values)
            if candidate_mapping.get("fio") is not None:
                header_mapping = candidate_mapping
                header_labels = [str(value).strip() if value is not None else "" for value in row_values]
                header_found = True
            continue

        if _is_row_empty(row_values) or _row_has_total(row_values):
            break

        row_data: dict[str, object] = {
            "fio": None,
            "birth": None,
            "coach": None,
            "place": None,
            "score_set": None,
            "score_sector20": None,
            "score_big_round": None,
        }
        for key in row_data:
            if key in header_mapping:
                row_data[key] = row_values[header_mapping[key]]
        rows.append(row_data)

    return header_labels, rows, header_mapping, header_found


def parse_first_table_from_xlsx(path: str) -> tuple[list[str], list[dict[str, object]]]:
    header_labels, rows, _, _ = _parse_first_table(path)
    return header_labels, rows


def parse_first_table_from_xlsx_with_report(path: str) -> ImportParseReport:
    headers, rows, header_mapping, header_found = _parse_first_table(path)
    warnings = validate_rows(rows)
    errors: list[str] = []

    if not header_found:
        errors.append("Не найден заголовок таблицы.")

    required_fields = {
        "fio": "ФИО",
        "place": "Место",
    }
    missing_required = [label for key, label in required_fields.items() if key not in header_mapping]
    for label in missing_required:
        errors.append(f"Не найден столбец {label}.")

    total_required = len(required_fields)
    found_required = total_required - len(missing_required)
    confidence = found_required / total_required if total_required else 0.0
    needs_mapping = confidence < 1.0

    return ImportParseReport(
        headers=headers,
        rows=rows,
        errors=errors,
        warnings=warnings,
        needs_mapping=needs_mapping,
        confidence=confidence,
    )


def _is_number(value: object) -> bool:
    if value is None or isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        try:
            float(value.replace(",", "."))
        except ValueError:
            return False
        return True
    return False


def validate_rows(rows: Iterable[dict[str, object]]) -> list[str]:
    warnings: list[str] = []
    numeric_fields = {
        "place": "место",
        "score_set": "очки (набор)",
        "score_sector20": "сектор 20",
        "score_big_round": "большой раунд",
    }
    for idx, row in enumerate(rows, start=1):
        fio = row.get("fio")
        if fio is None or str(fio).strip() == "":
            warnings.append(f"Строка {idx}: пустое ФИО")
        for field, label in numeric_fields.items():
            value = row.get(field)
            if value is None or str(value).strip() == "":
                continue
            if not _is_number(value):
                warnings.append(
                    f"Строка {idx}: поле '{label}' не число ({value})"
                )
    return warnings


def _normalize_text(value: object | None) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _parse_fio(value: object) -> tuple[str, str, str | None]:
    text = _normalize_text(value)
    parts = [part for part in text.split() if part]
    if not parts:
        return "", "", None
    last_name = parts[0]
    first_name = parts[1] if len(parts) > 1 else ""
    middle_name = " ".join(parts[2:]) if len(parts) > 2 else None
    return last_name, first_name, middle_name


def _parse_birth_value(value: object | None) -> tuple[str | None, str | None]:
    if value is None or _normalize_text(value) == "":
        return None, None
    if isinstance(value, datetime):
        return value.date().isoformat(), str(value.year)
    if isinstance(value, date):
        return value.isoformat(), str(value.year)
    if isinstance(value, (int, float)):
        year = int(value)
        if 1900 <= year <= 2100:
            return str(year), str(year)
        return None, None
    text = _normalize_text(value)
    if text.isdigit() and len(text) == 4:
        return text, text
    for fmt in ("%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            parsed = datetime.strptime(text, fmt).date()
        except ValueError:
            continue
        return parsed.isoformat(), str(parsed.year)
    return None, None


def _to_int(value: object | None) -> int | None:
    if value is None or _normalize_text(value) == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = _normalize_text(value).replace(",", ".")
    try:
        return int(float(text))
    except ValueError:
        return None


def parse_int(value: object | None) -> int | None:
    return _to_int(value)


def import_tournament_results(
    *,
    connection,
    file_path: str,
    tournament_name: str,
    tournament_date: str | None,
    category_code: str | None,
) -> tuple[int, bool]:
    _, rows = parse_first_table_from_xlsx(file_path)
    if not rows:
        raise ValueError("Не удалось найти таблицу в файле.")

    tournament_repo = TournamentRepository(connection)
    player_repo = PlayerRepository(connection)
    result_repo = ResultRepository(connection)
    norms, norms_loaded = load_norms_from_settings()

    tournament_id = tournament_repo.create(
        {
            "name": tournament_name,
            "date": tournament_date,
            "category_code": category_code,
            "league_code": None,
            "source_files": json.dumps([file_path]),
        }
    )

    for row in rows:
        fio = row.get("fio")
        if fio is None or _normalize_text(fio) == "":
            continue
        last_name, first_name, middle_name = _parse_fio(fio)
        birth_date, birth_year = _parse_birth_value(row.get("birth"))

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
                    "coach": _normalize_text(row.get("coach")) or None,
                    "club": None,
                    "notes": None,
                }
            )
        else:
            player_id = int(player["id"])

        place = _to_int(row.get("place"))
        score_set = _to_int(row.get("score_set"))
        score_sector20 = _to_int(row.get("score_sector20"))
        score_big_round = _to_int(row.get("score_big_round"))

        gender = None if player is None else player.get("gender")
        ranks, points_classification = calculate_points_classification(
            score_set=score_set,
            score_sector20=score_sector20,
            score_big_round=score_big_round,
            gender=gender,
            birth_date=birth_date,
            tournament_date=tournament_date,
            norms=norms or {},
        )
        points_place = points_for_place(place) if place is not None else 0
        points_total = points_place + points_classification

        result_repo.create(
            {
                "tournament_id": tournament_id,
                "player_id": player_id,
                "place": place,
                "score_set": score_set,
                "score_sector20": score_sector20,
                "score_big_round": score_big_round,
                "rank_set": ranks["rank_set"],
                "rank_sector20": ranks["rank_sector20"],
                "rank_big_round": ranks["rank_big_round"],
                "points_classification": points_classification,
                "points_place": points_place,
                "points_total": points_total,
                "calc_version": "v2",
            }
        )

    return tournament_id, norms_loaded

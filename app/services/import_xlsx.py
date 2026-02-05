from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from openpyxl import load_workbook


@dataclass(frozen=True)
class ParsedTable:
    headers: list[str]
    rows: list[dict[str, object]]


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


def parse_first_table_from_xlsx(path: str) -> tuple[list[str], list[dict[str, object]]]:
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

    return header_labels, rows


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

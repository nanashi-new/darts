from __future__ import annotations

import json
from pathlib import Path

from app.services.import_xlsx import (
    TableBlock,
    _calculate_mapping_stats,
    detect_headers,
    validate_rows,
)


# Field synonyms: map external JSON keys to internal keys
_FIELD_SYNONYMS: dict[str, list[str]] = {
    "fio": ["fio", "фио", "player", "игрок", "name", "имя", "фамилия", "фамилияимя"],
    "birth": ["birth", "др", "birth_date", "birth_year", "дата_рождения", "год_рождения", "рождения"],
    "coach": ["coach", "тренер"],
    "place": ["place", "место", "position", "позиция"],
    "score_set": ["score_set", "набор", "очки", "score", "результат"],
    "score_sector20": ["score_sector20", "с20", "sector20", "сектор20"],
    "score_big_round": ["score_big_round", "бр", "biground", "большойраунд", "br"],
}


def _normalize_key(value: str) -> str:
    text = value.strip().lower()
    return "".join(ch for ch in text if ch.isalnum() or ch == "_")


def _build_key_mapping(fields: list[str]) -> dict[str, str]:
    """Map JSON object keys to internal field names."""
    mapping: dict[str, str] = {}
    for field in fields:
        normalized = _normalize_key(field)
        if not normalized:
            continue
        for internal_key, synonyms in _FIELD_SYNONYMS.items():
            for synonym in synonyms:
                if normalized == _normalize_key(synonym):
                    mapping[field] = internal_key
                    break
            if field in mapping:
                break
    return mapping


def parse_tables_from_json(path: str) -> list[TableBlock]:
    """Parse a JSON file (array of objects) into TableBlock objects."""
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        return []

    try:
        raw = file_path.read_text(encoding="utf-8")
    except OSError:
        return []

    if not raw.strip():
        return []

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []

    if not isinstance(data, list):
        return []

    if not data:
        return []

    # All items must be dicts
    objects = [item for item in data if isinstance(item, dict)]
    if not objects:
        return []

    # Collect all keys from all objects
    all_keys: list[str] = []
    seen: set[str] = set()
    for obj in objects:
        for key in obj:
            if key not in seen:
                all_keys.append(key)
                seen.add(key)

    key_mapping = _build_key_mapping(all_keys)
    if not key_mapping:
        return []

    # Build header_mapping (internal_key -> column_index) for detect_headers compatibility
    header_index_mapping: dict[str, int] = {}
    for idx, key in enumerate(all_keys):
        internal = key_mapping.get(key)
        if internal is not None and internal not in header_index_mapping:
            header_index_mapping[internal] = idx

    # Parse rows
    rows: list[dict[str, object]] = []
    for obj in objects:
        row_data: dict[str, object] = {
            "fio": None,
            "birth": None,
            "coach": None,
            "place": None,
            "score_set": None,
            "score_sector20": None,
            "score_big_round": None,
        }
        for json_key, value in obj.items():
            internal_key = key_mapping.get(json_key)
            if internal_key is not None:
                row_data[internal_key] = value
        rows.append(row_data)

    if not rows:
        return []

    warnings = validate_rows(rows)
    missing_required, needs_mapping, confidence = _calculate_mapping_stats(header_index_mapping)
    errors: list[str] = []
    for label in missing_required:
        errors.append(f"Не найден столбец {label}.")

    source_to_internal = {
        key: key_mapping[key]
        for key in all_keys
        if key in key_mapping
    }

    return [
        TableBlock(
            sheet_name="json",
            start_row=1,
            end_row=len(rows),
            header_mapping=source_to_internal,
            rows=rows,
            warnings=warnings,
            errors=errors,
            needs_mapping=needs_mapping,
            confidence=confidence,
            missing_required_columns=missing_required,
        )
    ]

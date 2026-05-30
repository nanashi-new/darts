from __future__ import annotations

import csv
import io
from pathlib import Path

from app.services.import_xlsx import (
    TableBlock,
    _calculate_mapping_stats,
    detect_headers,
    validate_rows,
)


def parse_tables_from_csv(path: str) -> list[TableBlock]:
    """Parse a CSV file into TableBlock objects with auto-detected delimiter."""
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        return []

    try:
        raw_bytes = file_path.read_bytes()
    except OSError:
        return []

    if not raw_bytes.strip():
        return []

    # Handle UTF-8 BOM
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        text = raw_bytes.decode("utf-8-sig")
    else:
        text = raw_bytes.decode("utf-8", errors="replace")

    if not text.strip():
        return []

    delimiter = _detect_delimiter(text)

    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    all_rows: list[list[str]] = []
    for row in reader:
        all_rows.append(row)

    if not all_rows:
        return []

    # Find header row
    header_row_index: int | None = None
    header_mapping: dict[str, int] = {}
    for idx, row in enumerate(all_rows):
        candidate = detect_headers(row)
        if candidate.get("fio") is not None:
            header_mapping = candidate
            header_row_index = idx
            break

    if header_row_index is None:
        return []

    header_labels = all_rows[header_row_index]
    source_to_internal = {
        header_labels[col_idx]: key
        for key, col_idx in header_mapping.items()
        if 0 <= col_idx < len(header_labels)
    }

    # Parse data rows
    rows: list[dict[str, object]] = []
    for row in all_rows[header_row_index + 1:]:
        if not any(cell.strip() for cell in row):
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
        for key, col_idx in header_mapping.items():
            if col_idx < len(row):
                value = row[col_idx].strip() if row[col_idx].strip() else None
                row_data[key] = value
        rows.append(row_data)

    if not rows:
        return []

    warnings = validate_rows(rows)
    missing_required, needs_mapping, confidence = _calculate_mapping_stats(header_mapping)
    errors: list[str] = []
    for label in missing_required:
        errors.append(f"Не найден столбец {label}.")

    return [
        TableBlock(
            sheet_name="csv",
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


def _detect_delimiter(text: str) -> str:
    """Auto-detect CSV delimiter using csv.Sniffer, fallback to comma."""
    sample = text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        return dialect.delimiter
    except csv.Error:
        pass

    # Fallback: count occurrences in first few lines
    lines = sample.split("\n")[:5]
    best_delimiter = ","
    best_count = 0
    for delim in [",", ";", "\t"]:
        count = sum(line.count(delim) for line in lines)
        if count > best_count:
            best_count = count
            best_delimiter = delim
    return best_delimiter

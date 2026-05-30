from __future__ import annotations

from app.services.import_xlsx import (
    TableBlock,
    _calculate_mapping_stats,
    detect_headers,
    validate_rows,
)


def parse_tables_from_clipboard_text(text: str) -> list[TableBlock]:
    """Parse tab-separated clipboard text (Excel/Google Sheets format) into TableBlock objects."""
    if not text or not text.strip():
        return []

    lines = text.strip().split("\n")
    if not lines:
        return []

    # Split by tabs
    all_rows: list[list[str]] = []
    for line in lines:
        row = line.rstrip("\r").split("\t")
        all_rows.append(row)

    if not all_rows:
        return []

    # First row is headers
    header_row = all_rows[0]
    header_mapping = detect_headers(header_row)

    if header_mapping.get("fio") is None:
        return []

    header_labels = header_row
    source_to_internal = {
        header_labels[col_idx]: key
        for key, col_idx in header_mapping.items()
        if 0 <= col_idx < len(header_labels)
    }

    # Parse data rows
    rows: list[dict[str, object]] = []
    for row in all_rows[1:]:
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
            sheet_name="clipboard",
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

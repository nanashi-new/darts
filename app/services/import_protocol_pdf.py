from __future__ import annotations

import logging
import re
from pathlib import Path

from PyPDF2 import PdfReader

from app.services.import_xlsx import (
    TableBlock,
    validate_rows,
)

logger = logging.getLogger(__name__)

_CATEGORY_PATTERNS = re.compile(
    r"\b(мужчин|женщин|юниор|юниорк|мальчик|девочк|юнош|девуш|ветеран)",
    re.IGNORECASE,
)

# Pattern to detect a result line: starts with a place number (1-3 digits)
# followed by various data including birth year, scores, and FIO.
_PLACE_PREFIX = re.compile(r"^\s*(\d{1,3})\s+")

# 4-digit birth year pattern
_BIRTH_YEAR = re.compile(r"\b(19[5-9]\d|20[0-2]\d)\b")

# Date pattern dd.mm.yyyy
_BIRTH_DATE = re.compile(r"\b(\d{2}\.\d{2}\.\d{4})\b")

# FIO pattern: sequence of 2-3 Cyrillic words (last name + first name + optional patronymic)
_FIO_PATTERN = re.compile(r"([А-ЯЁа-яё]{2,}(?:\s+[А-ЯЁа-яё]{2,}){1,2})")

# Integer scores (1-4 digit numbers)
_SCORE_PATTERN = re.compile(r"\b(\d{1,4})\b")


def _is_category_line(line: str) -> str | None:
    """Check if a line contains a category header. Returns category name or None."""
    stripped = line.strip()
    if not stripped:
        return None
    if _CATEGORY_PATTERNS.search(stripped):
        # Category lines are typically short (just the category name)
        # Filter out lines that are clearly data rows (contain many numbers)
        digit_count = sum(1 for c in stripped if c.isdigit())
        if digit_count > 6:
            return None
        return stripped
    return None


def _parse_result_line(line: str) -> dict[str, object] | None:
    """Try to parse a result line into a row dict.

    Returns None if the line does not look like a result row.
    """
    stripped = line.strip()
    if not stripped:
        return None

    # Must start with a place number
    place_match = _PLACE_PREFIX.match(stripped)
    if not place_match:
        return None

    place = place_match.group(1)

    # Extract birth year or date
    birth: str | None = None
    birth_date_match = _BIRTH_DATE.search(stripped)
    if birth_date_match:
        birth = birth_date_match.group(1)
    else:
        birth_year_match = _BIRTH_YEAR.search(stripped)
        if birth_year_match:
            birth = birth_year_match.group(1)

    # Extract FIO - look for Cyrillic word sequences
    fio: str | None = None
    fio_matches = _FIO_PATTERN.findall(stripped)
    if fio_matches:
        # Take the longest match as FIO (most likely to be full name)
        fio = max(fio_matches, key=len)

    if not fio:
        return None

    # Extract scores: find all integers in the line, excluding place and birth year
    all_numbers = _SCORE_PATTERN.findall(stripped)
    # Filter out the place number and birth year from the list
    score_candidates: list[str] = []
    skip_values = {place}
    if birth and birth.isdigit():
        skip_values.add(birth)

    place_skipped = False
    birth_skipped = False
    for num in all_numbers:
        if num == place and not place_skipped:
            place_skipped = True
            continue
        if birth and num == birth and not birth_skipped:
            birth_skipped = True
            continue
        score_candidates.append(num)

    # Assign scores: typically the order is score_set, score_sector20, score_big_round, total
    score_set: str | None = None
    score_sector20: str | None = None
    score_big_round: str | None = None

    if len(score_candidates) >= 3:
        score_set = score_candidates[0]
        score_sector20 = score_candidates[1]
        score_big_round = score_candidates[2]
    elif len(score_candidates) == 2:
        score_set = score_candidates[0]
        score_sector20 = score_candidates[1]
    elif len(score_candidates) == 1:
        score_set = score_candidates[0]

    return {
        "fio": fio,
        "birth": birth,
        "coach": None,
        "place": place,
        "score_set": score_set,
        "score_sector20": score_sector20,
        "score_big_round": score_big_round,
    }


def parse_lines(text: str) -> tuple[list[dict[str, object]], list[str], str]:
    """Parse extracted PDF text into rows, warnings, and detected category.

    This is exposed as a testable helper function.
    Returns (rows, warnings, last_category_detected).
    """
    rows: list[dict[str, object]] = []
    warnings: list[str] = []
    current_category = ""

    for line in text.splitlines():
        cat = _is_category_line(line)
        if cat is not None:
            current_category = cat
            continue

        row = _parse_result_line(line)
        if row is not None:
            rows.append(row)
        else:
            # Only warn about lines that look like they might contain data
            stripped = line.strip()
            if stripped and any(c.isdigit() for c in stripped) and len(stripped) > 10:
                # Looks like it might be data but we couldn't parse it
                pass  # Skip silently for lines that are just noise

    return rows, warnings, current_category


def parse_tables_from_pdf(path: str) -> list[TableBlock]:
    """Parse a PDF protocol file into TableBlock objects.

    Extracts text from each page, detects category headers, and parses
    result rows containing place, FIO, birth, and scores.
    """
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        return []

    try:
        reader = PdfReader(path)
    except Exception as exc:
        logger.warning("Не удалось открыть PDF файл %s: %s", path, exc)
        return []

    if len(reader.pages) == 0:
        return []

    blocks: list[TableBlock] = []
    current_category = "Без категории"

    for page_num, page in enumerate(reader.pages):
        try:
            text = page.extract_text()
        except Exception as exc:
            logger.warning("Ошибка извлечения текста из страницы %d: %s", page_num + 1, exc)
            continue

        if not text:
            continue

        # Process line by line
        page_rows: list[dict[str, object]] = []
        page_warnings: list[str] = []

        for line in text.splitlines():
            cat = _is_category_line(line)
            if cat is not None:
                # If we have accumulated rows, save them as a block
                if page_rows:
                    block = _make_block(current_category, page_rows, page_warnings)
                    blocks.append(block)
                    page_rows = []
                    page_warnings = []
                current_category = cat
                continue

            row = _parse_result_line(line)
            if row is not None:
                page_rows.append(row)

        # End of page: save any accumulated rows
        if page_rows:
            block = _make_block(current_category, page_rows, page_warnings)
            blocks.append(block)

    return blocks


def _make_block(
    category: str,
    rows: list[dict[str, object]],
    warnings: list[str],
) -> TableBlock:
    """Create a TableBlock from parsed rows."""
    all_warnings = list(warnings)
    all_warnings.extend(validate_rows(rows))

    header_mapping: dict[str, str] = {
        "ФИО": "fio",
        "Дата рождения": "birth",
        "место": "place",
        "набор очков": "score_set",
        "сектор 20": "score_sector20",
        "Большой раунд": "score_big_round",
    }

    # Determine if we have scores
    has_scores = any(
        row.get("score_set") is not None
        for row in rows
    )

    missing: list[str] = []
    if not has_scores:
        missing = ["набор очков", "сектор 20", "Большой раунд"]

    return TableBlock(
        sheet_name=category,
        start_row=1,
        end_row=len(rows),
        header_mapping=header_mapping,
        rows=rows,
        warnings=all_warnings,
        errors=[],
        needs_mapping=not has_scores,
        confidence=0.8 if has_scores else 0.5,
        missing_required_columns=missing,
    )

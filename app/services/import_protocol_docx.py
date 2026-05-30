from __future__ import annotations

import logging
import re
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

from app.services.import_xlsx import (
    TableBlock,
    validate_rows,
)

logger = logging.getLogger(__name__)

_CATEGORY_PATTERNS = re.compile(
    r"(юниор|юниорк|мужчин|женщин|мальчик|девочк|юнош|девуш|ветеран)",
    re.IGNORECASE,
)

_JURY_KEYWORDS = {"должность", "фио", "город", "формат"}


def _is_jury_table(table) -> bool:  # type: ignore[no-untyped-def]
    """Determine if a table is a jury table (4 columns, contains jury keywords)."""
    try:
        rows = table.rows
        if not rows:
            return False
        first_row_cells = rows[0].cells
        col_count = len(first_row_cells)
        if col_count == 4:
            cell_texts = {cell.text.strip().lower() for cell in first_row_cells}
            if cell_texts & _JURY_KEYWORDS:
                return True
        return False
    except Exception:
        return False


def _extract_category(text: str) -> str | None:
    """Extract category name from paragraph text if it matches known patterns."""
    stripped = text.strip()
    if not stripped:
        return None
    if _CATEGORY_PATTERNS.search(stripped):
        return stripped
    return None


def _get_cell_text(cell) -> str:  # type: ignore[no-untyped-def]
    """Get stripped text from a cell."""
    return cell.text.strip() if cell.text else ""


def _get_first_nonempty(cells, start: int, end: int) -> str:
    """Get first non-empty text from a range of cells."""
    for i in range(start, min(end, len(cells))):
        text = _get_cell_text(cells[i])
        if text:
            return text
    return ""


def _parse_501_table(table, category: str) -> TableBlock | None:  # type: ignore[no-untyped-def]
    """Parse a 501-format results table (7 columns)."""
    rows_data: list[dict[str, object]] = []
    warnings: list[str] = []

    table_rows = table.rows
    if len(table_rows) < 2:
        return None

    # Skip header row(s)
    data_start = 1
    for row in table_rows[data_start:]:
        try:
            cells = row.cells
            if len(cells) < 7:
                continue

            place_text = _get_cell_text(cells[0])
            fio_text = _get_cell_text(cells[1])
            birth_text = _get_cell_text(cells[2])
            coach_text = _get_cell_text(cells[5])

            if not fio_text:
                continue

            row_data: dict[str, object] = {
                "fio": fio_text or None,
                "birth": birth_text or None,
                "coach": coach_text or None,
                "place": place_text or None,
                "score_set": None,
                "score_sector20": None,
                "score_big_round": None,
            }
            rows_data.append(row_data)
        except Exception as exc:
            warnings.append(f"Ошибка разбора строки: {exc}")

    if not rows_data:
        return None

    warnings.extend(validate_rows(rows_data))

    header_mapping: dict[str, str] = {
        "Фамилия, Имя": "fio",
        "Год рождения": "birth",
        "тренер": "coach",
        "МЕСТО": "place",
    }

    return TableBlock(
        sheet_name=category,
        start_row=1,
        end_row=len(rows_data),
        header_mapping=header_mapping,
        rows=rows_data,
        warnings=warnings,
        errors=[],
        needs_mapping=True,
        confidence=0.67,
        missing_required_columns=["Очки", "Сектор 20", "Большой раунд"],
    )


def _parse_classification_table(table, category: str) -> TableBlock | None:  # type: ignore[no-untyped-def]
    """Parse a classification-format results table (16 columns with merged cells)."""
    rows_data: list[dict[str, object]] = []
    warnings: list[str] = []

    table_rows = table.rows
    if len(table_rows) < 2:
        return None

    # Skip header row(s) - might be 1 or 2 rows of headers
    data_start = 1
    # Check if second row is also a header (contains sub-headers like "попытка 1")
    if len(table_rows) > 2:
        second_row_cells = table_rows[1].cells
        second_text = " ".join(_get_cell_text(c) for c in second_row_cells).lower()
        if "попытка" in second_text or "1" == _get_cell_text(second_row_cells[0]).strip():
            # Could be sub-header, but often row with "1" in first cell is data
            # Check more carefully
            if "попытка" in second_text:
                data_start = 2

    for row in table_rows[data_start:]:
        try:
            cells = row.cells
            num_cells = len(cells)
            if num_cells < 10:
                continue

            place_text = _get_cell_text(cells[0])
            # FIO: cols 1-3 (merged), take first non-empty
            fio_text = _get_first_nonempty(cells, 1, 4)
            # Birth: col 4
            birth_text = _get_cell_text(cells[4]) if num_cells > 4 else ""
            # Coach: cols 5-7 (merged), take first non-empty
            coach_text = _get_first_nonempty(cells, 5, 8)

            # Scores depend on actual column count
            score_set: str | None = None
            score_sector20: str | None = None
            score_big_round: str | None = None

            if num_cells >= 16:
                # Full 16-column layout
                score_set = _get_first_nonempty(cells, 8, 10) or None
                score_sector20 = _get_first_nonempty(cells, 10, 12) or None
                score_big_round = _get_first_nonempty(cells, 12, 14) or None
            elif num_cells >= 13:
                score_set = _get_first_nonempty(cells, 7, 9) or None
                score_sector20 = _get_first_nonempty(cells, 9, 11) or None
                score_big_round = _get_first_nonempty(cells, 11, 13) or None
            elif num_cells >= 10:
                score_set = _get_cell_text(cells[7]) or None
                score_sector20 = _get_cell_text(cells[8]) or None
                score_big_round = _get_cell_text(cells[9]) or None

            if not fio_text:
                continue

            row_data: dict[str, object] = {
                "fio": fio_text or None,
                "birth": birth_text or None,
                "coach": coach_text or None,
                "place": place_text or None,
                "score_set": score_set,
                "score_sector20": score_sector20,
                "score_big_round": score_big_round,
            }
            rows_data.append(row_data)
        except Exception as exc:
            warnings.append(f"Ошибка разбора строки: {exc}")

    if not rows_data:
        return None

    warnings.extend(validate_rows(rows_data))

    header_mapping: dict[str, str] = {
        "ФИО": "fio",
        "Г/Р": "birth",
        "тренер": "coach",
        "место": "place",
        "набор очков": "score_set",
        "сектор 20": "score_sector20",
        "Большой раунд": "score_big_round",
    }

    return TableBlock(
        sheet_name=category,
        start_row=1,
        end_row=len(rows_data),
        header_mapping=header_mapping,
        rows=rows_data,
        warnings=warnings,
        errors=[],
        needs_mapping=False,
        confidence=1.0,
        missing_required_columns=[],
    )


def _detect_table_type(table) -> str:  # type: ignore[no-untyped-def]
    """Detect if a results table is '501' or 'classification' format.

    Returns 'jury', '501', 'classification', or 'unknown'.
    """
    if _is_jury_table(table):
        return "jury"

    try:
        rows = table.rows
        if not rows:
            return "unknown"

        first_row_cells = rows[0].cells
        col_count = len(first_row_cells)

        if col_count <= 4:
            return "jury"
        elif col_count <= 8:
            # Check header text for 501 indicators
            header_text = " ".join(_get_cell_text(c) for c in first_row_cells).lower()
            if "фамилия" in header_text or "звание" in header_text or "субъект" in header_text:
                return "501"
            # Default for 7 cols
            if col_count == 7:
                return "501"
            return "unknown"
        else:
            # 9+ columns - likely classification
            return "classification"
    except Exception:
        return "unknown"


def parse_tables_from_docx(path: str) -> list[TableBlock]:
    """Parse a DOCX protocol file into TableBlock objects.

    The DOCX structure contains pairs of tables (jury + results)
    with category names in paragraphs between pairs.
    """
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        return []

    try:
        doc = Document(path)
    except Exception as exc:
        logger.warning("Не удалось открыть DOCX файл %s: %s", path, exc)
        return []

    blocks: list[TableBlock] = []
    current_category = "Без категории"

    # Iterate over document body children to get paragraphs and tables in order
    body = doc.element.body
    tables_iter = iter(doc.tables)

    for child in body:
        tag = child.tag
        if tag == qn("w:p"):
            # Paragraph - check for category name
            text = child.text or ""
            # Also check runs within the paragraph
            if not text.strip():
                runs = child.findall(qn("w:r"))
                parts: list[str] = []
                for run in runs:
                    t_elements = run.findall(qn("w:t"))
                    for t_el in t_elements:
                        if t_el.text:
                            parts.append(t_el.text)
                text = "".join(parts)

            category = _extract_category(text)
            if category:
                current_category = category

        elif tag == qn("w:tbl"):
            # Table element - get the corresponding python-docx Table
            try:
                table = next(tables_iter)
            except StopIteration:
                break

            try:
                table_type = _detect_table_type(table)

                if table_type == "jury":
                    logger.debug("Пропуск таблицы жюри в категории '%s'", current_category)
                    continue
                elif table_type == "501":
                    block = _parse_501_table(table, current_category)
                    if block is not None:
                        blocks.append(block)
                elif table_type == "classification":
                    block = _parse_classification_table(table, current_category)
                    if block is not None:
                        blocks.append(block)
                else:
                    logger.debug(
                        "Пропуск таблицы неизвестного типа в категории '%s'",
                        current_category,
                    )
            except Exception as exc:
                logger.warning(
                    "Ошибка разбора таблицы в категории '%s': %s",
                    current_category,
                    exc,
                )

    return blocks

from __future__ import annotations

from pathlib import Path
from typing import Iterable
from uuid import uuid4

from openpyxl import Workbook


def _next_path(tmp_path: Path, prefix: str) -> Path:
    return tmp_path / f"{prefix}_{uuid4().hex}.xlsx"


def make_single_table_xlsx(
    tmp_path: Path,
    headers: Iterable[object],
    rows: Iterable[Iterable[object]],
    sheet: str = "Sheet1",
) -> Path:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = sheet

    worksheet.append(list(headers))
    for row in rows:
        worksheet.append(list(row))

    path = _next_path(tmp_path, "single_table")
    workbook.save(path)
    return path


def make_multi_table_xlsx(
    tmp_path: Path,
    blocks: Iterable[dict[str, object]],
    sheet: str = "Sheet1",
    gap_rows: int = 2,
) -> Path:
    blocks_list = list(blocks)
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = sheet

    for block_index, block in enumerate(blocks_list):
        title = block.get("title")
        headers = block.get("headers", [])
        rows = block.get("rows", [])

        if title:
            worksheet.append([title])
        worksheet.append(list(headers))
        for row in rows:
            worksheet.append(list(row))

        if block_index < len(blocks_list) - 1:
            for _ in range(max(gap_rows, 0)):
                worksheet.append([])

    path = _next_path(tmp_path, "multi_table")
    workbook.save(path)
    return path

from __future__ import annotations

import pytest

from app.services.import_xlsx import parse_first_table_from_xlsx_with_report
from tests.helpers.xlsx_factory import make_multi_table_xlsx


@pytest.mark.xfail(reason="Multi-table XLSX detection not implemented yet.")
def test_parse_multi_table_blocks_expected_fail(tmp_path) -> None:
    blocks = [
        {
            "title": "Категория U12",
            "headers": ["ФИО", "Место", "Очки"],
            "rows": [["Иванов Иван", 1, 100]],
        },
        {
            "title": "Категория U14",
            "headers": ["ФИО", "Место", "Очки"],
            "rows": [["Петров Петр", 2, 90]],
        },
    ]
    path = make_multi_table_xlsx(tmp_path, blocks, gap_rows=2)

    report = parse_first_table_from_xlsx_with_report(str(path))

    assert report.errors == []
    assert len(report.rows) == 2

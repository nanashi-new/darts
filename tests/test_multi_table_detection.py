from __future__ import annotations

from app.services.import_xlsx import parse_tables_from_xlsx_with_report
from tests.helpers.xlsx_factory import make_multi_table_xlsx


import pytest

pytestmark = pytest.mark.integration

def test_parse_multi_table_blocks(tmp_path) -> None:
    blocks = [
        {
            "title": "Категория U12",
            "headers": ["ФИО", "Дата рождения", "Место", "Набор очков", "Сектор 20", "Большой раунд"],
            "rows": [["Иванов Иван", "2012-01-02", 1, 100, 45, 78]],
        },
        {
            "title": "Категория U14",
            "headers": ["ФИО", "Дата рождения", "Место", "Набор очков", "Сектор 20", "Большой раунд"],
            "rows": [["Петров Петр", "2011-02-03", 2, 90, 38, 70]],
        },
    ]
    path = make_multi_table_xlsx(tmp_path, blocks, gap_rows=2)

    parsed = parse_tables_from_xlsx_with_report(str(path))

    assert len(parsed) == 2
    assert parsed[0].errors == []
    assert parsed[1].errors == []
    assert len(parsed[0].rows) == 1
    assert len(parsed[1].rows) == 1

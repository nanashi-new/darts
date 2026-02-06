from __future__ import annotations

from openpyxl import Workbook

from app.services.import_xlsx import import_batch_from_folder
from tests.helpers.xlsx_factory import make_single_table_xlsx


def test_batch_import(tmp_path) -> None:
    good_headers = ["ФИО", "Место", "Очки"]
    good_rows = [["Иванов Иван", 1, 100]]
    make_single_table_xlsx(tmp_path, good_headers, good_rows)
    make_single_table_xlsx(tmp_path, good_headers, good_rows)

    empty_path = tmp_path / "empty.xlsx"
    Workbook().save(empty_path)

    result = import_batch_from_folder(str(tmp_path))

    assert result["success"] == 2
    assert result["error"] == 1
    assert len(result["items"]) == 3

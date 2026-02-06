from __future__ import annotations

import pytest

from openpyxl import Workbook

from app.services import import_xlsx as import_module
from tests.helpers.xlsx_factory import make_single_table_xlsx


@pytest.mark.xfail(reason="Batch import not implemented yet.")
def test_batch_import_stub(tmp_path) -> None:
    good_headers = ["ФИО", "Место", "Очки"]
    good_rows = [["Иванов Иван", 1, 100]]
    make_single_table_xlsx(tmp_path, good_headers, good_rows)
    make_single_table_xlsx(tmp_path, good_headers, good_rows)

    empty_path = tmp_path / "empty.xlsx"
    Workbook().save(empty_path)

    if not hasattr(import_module, "import_batch_from_folder"):
        pytest.xfail("Batch import service not available yet.")

    result = import_module.import_batch_from_folder(str(tmp_path))

    assert result["success"] == 2
    assert result["error"] == 1

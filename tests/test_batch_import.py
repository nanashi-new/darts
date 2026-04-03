from __future__ import annotations

from openpyxl import Workbook

from app.services.import_xlsx import import_batch_from_folder
from tests.helpers.xlsx_factory import make_single_table_xlsx


import pytest

pytestmark = pytest.mark.integration

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


def test_batch_import_empty_folder(tmp_path) -> None:
    result = import_batch_from_folder(str(tmp_path))

    assert result["success"] == 0
    assert result["error"] == 0
    assert result["items"] == []


def test_batch_import_invalid_folder_path(tmp_path) -> None:
    missing_folder = tmp_path / "missing"

    result = import_batch_from_folder(str(missing_folder))

    assert result["success"] == 0
    assert result["error"] == 1
    assert result["items"] == [
        {
            "path": str(missing_folder),
            "status": "error",
            "message": "Путь не существует.",
            "tables": 0,
        }
    ]


def test_batch_import_file_path_instead_of_folder(tmp_path) -> None:
    file_path = tmp_path / "data.xlsx"
    Workbook().save(file_path)

    result = import_batch_from_folder(str(file_path))

    assert result["success"] == 0
    assert result["error"] == 1
    assert result["items"] == [
        {
            "path": str(file_path),
            "status": "error",
            "message": "Указанный путь не является директорией.",
            "tables": 0,
        }
    ]

from __future__ import annotations

from app.services.import_xlsx import parse_first_table_from_xlsx_with_report, parse_int
from tests.helpers.xlsx_factory import make_single_table_xlsx


def test_parse_single_table_happy_path(tmp_path) -> None:
    headers = ["ФИО", "Год рождения", "Место", "Очки", "С20", "БР"]
    rows = [
        ["Иванов Иван", 2010, 1, 150, 50, 25],
        ["Петров Петр", "", 2, "", 40, 20],
    ]
    path = make_single_table_xlsx(tmp_path, headers, rows)

    report = parse_first_table_from_xlsx_with_report(str(path))

    assert report.errors == []
    assert report.warnings == []
    assert len(report.rows) == 2
    assert all(row.get("fio") for row in report.rows)

    first_row = report.rows[0]
    second_row = report.rows[1]

    assert parse_int(first_row.get("place")) == 1
    assert parse_int(first_row.get("score_set")) == 150
    assert parse_int(first_row.get("score_sector20")) == 50
    assert parse_int(first_row.get("score_big_round")) == 25

    assert parse_int(second_row.get("place")) == 2
    assert parse_int(second_row.get("score_set")) is None


def test_parse_single_table_reports_missing_fio(tmp_path) -> None:
    headers = ["ФИО", "Место", "Очки"]
    rows = [
        ["", 1, 100],
        ["Петров Петр", 2, 90],
    ]
    path = make_single_table_xlsx(tmp_path, headers, rows)

    report = parse_first_table_from_xlsx_with_report(str(path))

    assert any("пустое ФИО" in warning for warning in report.warnings)

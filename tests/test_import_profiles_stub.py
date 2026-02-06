from __future__ import annotations

from app.services.import_xlsx import parse_first_table_from_xlsx_with_report
from tests.helpers.xlsx_factory import make_single_table_xlsx


def test_import_profiles_needs_mapping_for_nonstandard_headers(tmp_path) -> None:
    headers = ["Игрок (ФИО)", "Place", "Очки"]
    rows = [
        ["Иванов Иван", 1, 100],
        ["Петров Петр", 2, 90],
    ]
    path = make_single_table_xlsx(tmp_path, headers, rows)

    report = parse_first_table_from_xlsx_with_report(str(path))

    assert report.needs_mapping is True
    assert report.confidence < 1.0
    assert any("ФИО" in message for message in report.errors)

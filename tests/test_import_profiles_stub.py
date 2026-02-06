from __future__ import annotations

from app.services.import_xlsx import (
    ImportProfile,
    apply_profile_to_headers,
    parse_first_table_from_xlsx_with_report,
)
from tests.helpers.xlsx_factory import make_single_table_xlsx


def test_import_profiles_needs_mapping_for_nonstandard_headers(tmp_path) -> None:
    headers = ["Участник", "Позиция", "Набранные баллы"]
    rows = [
        ["Иванов Иван", 1, 100],
        ["Петров Петр", 2, 90],
    ]
    path = make_single_table_xlsx(tmp_path, headers, rows)

    report = parse_first_table_from_xlsx_with_report(str(path))

    assert report.needs_mapping is True
    assert report.confidence < 1.0


def test_apply_profile_to_headers_improves_confidence_for_custom_aliases() -> None:
    headers = ["Участник", "Позиция", "Набранные баллы", "Год"]
    profile = ImportProfile(
        name="custom",
        required_columns=["fio", "place", "score_set"],
        header_aliases={
            "fio": ["Участник"],
            "place": ["Позиция"],
            "score_set": ["Набранные баллы"],
            "birth_year": ["Год"],
        },
    )

    mapping, confidence = apply_profile_to_headers(profile, headers)

    assert mapping["Участник"] == "fio"
    assert mapping["Позиция"] == "place"
    assert mapping["Набранные баллы"] == "score_set"
    assert confidence == 1.0

from __future__ import annotations

from app.services.category_suggestion import suggest_category_code


def test_suggest_category_code_uses_customer_age_groups() -> None:
    assert suggest_category_code(birth_date_or_year="2014-05-01", tournament_date="2024-05-01") == "U10"
    assert suggest_category_code(birth_date_or_year="2012", tournament_date="2024-05-01") == "U12"
    assert suggest_category_code(birth_date_or_year="2009-01-01", tournament_date="2024-05-01") == "U15"
    assert suggest_category_code(birth_date_or_year="2007-01-01", tournament_date="2024-05-01") == "JUNIOR"


def test_suggest_category_code_applies_gender_suffix_when_known() -> None:
    assert (
        suggest_category_code(
            birth_date_or_year="2014-05-01",
            tournament_date="2024-05-01",
            gender="мужской",
        )
        == "U10-M"
    )
    assert (
        suggest_category_code(
            birth_date_or_year="2012-05-01",
            tournament_date="2024-05-01",
            gender="женский",
        )
        == "U12-W"
    )


def test_suggest_category_code_does_not_force_adult_or_invalid_values() -> None:
    assert suggest_category_code(birth_date_or_year="2000-01-01", tournament_date="2024-05-01") is None
    assert suggest_category_code(birth_date_or_year=None, tournament_date="2024-05-01") is None
    assert suggest_category_code(birth_date_or_year="2012", tournament_date="bad") is None

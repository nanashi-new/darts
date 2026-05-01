from __future__ import annotations

from datetime import date, datetime


def suggest_category_code(
    *,
    birth_date_or_year: object | None,
    tournament_date: object | None,
    gender: object | None = None,
) -> str | None:
    birth_year, has_full_birth_date, birth_date = _parse_birth(birth_date_or_year)
    tournament = _parse_date(tournament_date)
    if birth_year is None or tournament is None:
        return None

    age = tournament.year - birth_year
    if has_full_birth_date and birth_date is not None:
        if (tournament.month, tournament.day) < (birth_date.month, birth_date.day):
            age -= 1

    if age < 0 or age > 120:
        return None

    if age <= 10:
        base = "U10"
    elif age <= 12:
        base = "U12"
    elif age <= 15:
        base = "U15"
    elif age <= 18:
        base = "JUNIOR"
    else:
        return None

    suffix = _gender_suffix(gender)
    return f"{base}-{suffix}" if suffix else base


def _parse_birth(value: object | None) -> tuple[int | None, bool, date | None]:
    if value is None:
        return None, False, None
    if isinstance(value, datetime):
        return value.year, True, value.date()
    if isinstance(value, date):
        return value.year, True, value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        year = int(value)
        if year == value:
            return year, False, None
        return None, False, None

    text = str(value).strip()
    if not text:
        return None, False, None
    if text.isdigit() and len(text) == 4:
        return int(text), False, None

    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            parsed = datetime.strptime(text, fmt).date()
        except ValueError:
            continue
        return parsed.year, True, parsed
    return None, False, None


def _parse_date(value: object | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _gender_suffix(value: object | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().lower()
    men = {"m", "male", "man", "men", "м", "муж", "мужской", "юноша"}
    women = {"f", "w", "female", "woman", "women", "ж", "жен", "женский", "девушка"}
    if normalized in men:
        return "M"
    if normalized in women:
        return "W"
    return None

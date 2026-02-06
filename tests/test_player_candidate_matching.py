from __future__ import annotations

from app.db.database import get_connection
from app.db.repositories import PlayerRepository
from app.services.import_xlsx import find_player_candidates


def test_find_player_candidates_normalizes_fio_and_birth_year(tmp_path) -> None:
    connection = get_connection(tmp_path / "players.db")
    repo = PlayerRepository(connection)
    repo.create(
        {
            "last_name": "Семенов",
            "first_name": "Петр",
            "middle_name": "Игоревич",
            "birth_date": "2010-05-12",
            "gender": None,
            "coach": None,
            "club": None,
            "notes": None,
        }
    )

    candidates = find_player_candidates(
        fio="  СЕМЁНОВ   ПЕТР   ИГОРЕВИЧ ",
        birth_date_or_year="2010",
        player_repo=repo,
    )

    assert len(candidates) == 1
    assert candidates[0]["last_name"] == "Семенов"


def test_find_player_candidates_returns_two_for_same_fio(tmp_path) -> None:
    connection = get_connection(tmp_path / "players.db")
    repo = PlayerRepository(connection)

    repo.create(
        {
            "last_name": "Иванов",
            "first_name": "Иван",
            "middle_name": None,
            "birth_date": "2010-01-01",
            "gender": None,
            "coach": "Тренер 1",
            "club": "Клуб 1",
            "notes": None,
        }
    )
    repo.create(
        {
            "last_name": "Иванов",
            "first_name": "Иван",
            "middle_name": None,
            "birth_date": "2010-11-11",
            "gender": None,
            "coach": "Тренер 2",
            "club": "Клуб 2",
            "notes": None,
        }
    )

    candidates = find_player_candidates(
        fio="Иванов Иван",
        birth_date_or_year="2010",
        player_repo=repo,
    )

    assert len(candidates) == 2

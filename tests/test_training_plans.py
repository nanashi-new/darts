from __future__ import annotations

import pytest

from app.db.database import get_connection
from app.db.repositories import PlayerRepository


pytestmark = pytest.mark.integration


def _make_connection(tmp_path):
    return get_connection(tmp_path / "training-plans.db")


def _create_player(connection) -> int:
    return PlayerRepository(connection).create(
        {
            "last_name": "Козлова",
            "first_name": "Анна",
            "middle_name": "Викторовна",
            "birth_date": "2011-03-20",
            "gender": "F",
            "coach": None,
            "club": None,
            "notes": None,
        }
    )


def test_create_training_plan_valid(tmp_path) -> None:
    connection = _make_connection(tmp_path)
    player_id = _create_player(connection)

    from app.services.training_plans import create_training_plan, get_training_plan

    plan_id = create_training_plan(
        connection=connection,
        player_id=player_id,
        title="План подготовки к турниру",
        description="Подготовительный план на 4 недели",
        goal="Улучшить точность на 15%",
        start_date="2026-06-01",
        end_date="2026-06-28",
        exercises=[
            {"name": "Удвоения", "sets": 5, "reps": 20},
            {"name": "Булл", "sets": 3, "reps": 10},
        ],
    )

    assert plan_id > 0
    plan = get_training_plan(connection=connection, plan_id=plan_id)
    assert plan is not None
    assert plan.title == "План подготовки к турниру"
    assert plan.player_id == player_id
    assert plan.status == "active"
    assert plan.goal == "Улучшить точность на 15%"
    assert plan.start_date == "2026-06-01"
    assert plan.end_date == "2026-06-28"
    assert "Козлова" in plan.player_fio


def test_create_training_plan_validation_error(tmp_path) -> None:
    connection = _make_connection(tmp_path)
    player_id = _create_player(connection)

    from app.services.training_plans import create_training_plan

    with pytest.raises(ValueError, match="Укажите название плана тренировок"):
        create_training_plan(connection=connection, player_id=player_id, title="  ")


def test_list_training_plans_filter_by_status(tmp_path) -> None:
    connection = _make_connection(tmp_path)
    player_id = _create_player(connection)

    from app.services.training_plans import create_training_plan, list_training_plans

    create_training_plan(connection=connection, player_id=player_id, title="Active plan", status="active")
    create_training_plan(connection=connection, player_id=player_id, title="Paused plan", status="paused")

    active = list_training_plans(connection=connection, status="active")
    assert len(active) == 1
    assert active[0].title == "Active plan"

    paused = list_training_plans(connection=connection, status="paused")
    assert len(paused) == 1
    assert paused[0].title == "Paused plan"


def test_list_training_plans_filter_by_player(tmp_path) -> None:
    connection = _make_connection(tmp_path)
    player_id = _create_player(connection)
    player_id_2 = PlayerRepository(connection).create(
        {
            "last_name": "Петров",
            "first_name": "Дмитрий",
            "middle_name": None,
            "birth_date": None,
            "gender": "M",
            "coach": None,
            "club": None,
            "notes": None,
        }
    )

    from app.services.training_plans import create_training_plan, list_training_plans

    create_training_plan(connection=connection, player_id=player_id, title="Plan for player 1")
    create_training_plan(connection=connection, player_id=player_id_2, title="Plan for player 2")

    plans_p1 = list_training_plans(connection=connection, player_id=player_id)
    assert len(plans_p1) == 1
    assert plans_p1[0].title == "Plan for player 1"


def test_update_training_plan(tmp_path) -> None:
    connection = _make_connection(tmp_path)
    player_id = _create_player(connection)

    from app.services.training_plans import (
        create_training_plan,
        update_training_plan,
        get_training_plan,
    )

    plan_id = create_training_plan(
        connection=connection,
        player_id=player_id,
        title="Original title",
        exercises=[{"name": "Exercise 1"}],
    )
    update_training_plan(
        plan_id,
        connection=connection,
        title="Updated title",
        status="completed",
        exercises=[{"name": "Exercise 1"}, {"name": "Exercise 2"}],
    )

    plan = get_training_plan(connection=connection, plan_id=plan_id)
    assert plan is not None
    assert plan.title == "Updated title"
    assert plan.status == "completed"
    assert len(plan.exercises) == 2
    assert plan.exercises[1]["name"] == "Exercise 2"


def test_delete_training_plan(tmp_path) -> None:
    connection = _make_connection(tmp_path)
    player_id = _create_player(connection)

    from app.services.training_plans import (
        create_training_plan,
        delete_training_plan,
        get_training_plan,
    )

    plan_id = create_training_plan(
        connection=connection,
        player_id=player_id,
        title="To delete",
    )
    delete_training_plan(connection=connection, plan_id=plan_id)

    plan = get_training_plan(connection=connection, plan_id=plan_id)
    assert plan is None


def test_exercises_stored_as_list(tmp_path) -> None:
    connection = _make_connection(tmp_path)
    player_id = _create_player(connection)

    from app.services.training_plans import create_training_plan, get_training_plan

    exercises_data = [
        {"name": "Сектор 20", "sets": 3, "reps": 15},
        {"name": "Булл", "sets": 5, "reps": 10},
    ]
    plan_id = create_training_plan(
        connection=connection,
        player_id=player_id,
        title="Exercises test",
        exercises=exercises_data,
    )

    plan = get_training_plan(connection=connection, plan_id=plan_id)
    assert plan is not None
    assert isinstance(plan.exercises, list)
    assert len(plan.exercises) == 2
    assert plan.exercises[0]["name"] == "Сектор 20"
    assert plan.exercises[1]["reps"] == 10

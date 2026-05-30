from __future__ import annotations

import pytest

from app.db.database import get_connection
from app.db.repositories import PlayerRepository


pytestmark = pytest.mark.integration


def _make_connection(tmp_path):
    return get_connection(tmp_path / "coach-tasks.db")


def _create_player(connection) -> int:
    return PlayerRepository(connection).create(
        {
            "last_name": "Иванов",
            "first_name": "Петр",
            "middle_name": "Сергеевич",
            "birth_date": "2010-05-15",
            "gender": "M",
            "coach": None,
            "club": None,
            "notes": None,
        }
    )


def test_create_coach_task_valid(tmp_path) -> None:
    connection = _make_connection(tmp_path)
    player_id = _create_player(connection)

    from app.services.coach_tasks import create_coach_task, get_coach_task

    task_id = create_coach_task(
        connection=connection,
        player_id=player_id,
        title="Отработать удвоения",
        description="Тренировка финишных бросков",
        due_date="2026-06-01",
        priority="high",
        category="technique",
    )

    assert task_id > 0
    task = get_coach_task(connection=connection, task_id=task_id)
    assert task is not None
    assert task.title == "Отработать удвоения"
    assert task.player_id == player_id
    assert task.status == "open"
    assert task.priority == "high"
    assert task.category == "technique"
    assert task.due_date == "2026-06-01"
    assert "Иванов" in task.player_fio


def test_create_coach_task_validation_error(tmp_path) -> None:
    connection = _make_connection(tmp_path)

    from app.services.coach_tasks import create_coach_task

    with pytest.raises(ValueError, match="Укажите название задачи"):
        create_coach_task(connection=connection, title="   ")


def test_list_coach_tasks_filter_by_status(tmp_path) -> None:
    connection = _make_connection(tmp_path)
    player_id = _create_player(connection)

    from app.services.coach_tasks import create_coach_task, list_coach_tasks

    create_coach_task(connection=connection, player_id=player_id, title="Task open", status="open")
    create_coach_task(connection=connection, player_id=player_id, title="Task in progress", status="in_progress")

    open_tasks = list_coach_tasks(connection=connection, status="open")
    assert len(open_tasks) == 1
    assert open_tasks[0].title == "Task open"

    in_progress_tasks = list_coach_tasks(connection=connection, status="in_progress")
    assert len(in_progress_tasks) == 1
    assert in_progress_tasks[0].title == "Task in progress"


def test_list_coach_tasks_filter_by_priority(tmp_path) -> None:
    connection = _make_connection(tmp_path)
    player_id = _create_player(connection)

    from app.services.coach_tasks import create_coach_task, list_coach_tasks

    create_coach_task(connection=connection, player_id=player_id, title="Low prio", priority="low")
    create_coach_task(connection=connection, player_id=player_id, title="Urgent prio", priority="urgent")

    urgent = list_coach_tasks(connection=connection, priority="urgent")
    assert len(urgent) == 1
    assert urgent[0].title == "Urgent prio"


def test_list_coach_tasks_filter_by_player(tmp_path) -> None:
    connection = _make_connection(tmp_path)
    player_id = _create_player(connection)
    player_id_2 = PlayerRepository(connection).create(
        {
            "last_name": "Сидоров",
            "first_name": "Алексей",
            "middle_name": None,
            "birth_date": None,
            "gender": "M",
            "coach": None,
            "club": None,
            "notes": None,
        }
    )

    from app.services.coach_tasks import create_coach_task, list_coach_tasks

    create_coach_task(connection=connection, player_id=player_id, title="Task for player 1")
    create_coach_task(connection=connection, player_id=player_id_2, title="Task for player 2")

    tasks_p1 = list_coach_tasks(connection=connection, player_id=player_id)
    assert len(tasks_p1) == 1
    assert tasks_p1[0].title == "Task for player 1"


def test_complete_coach_task(tmp_path) -> None:
    connection = _make_connection(tmp_path)
    player_id = _create_player(connection)

    from app.services.coach_tasks import create_coach_task, complete_coach_task, get_coach_task

    task_id = create_coach_task(connection=connection, player_id=player_id, title="To complete")
    complete_coach_task(task_id, connection=connection)

    task = get_coach_task(connection=connection, task_id=task_id)
    assert task is not None
    assert task.status == "done"
    assert task.completed_at is not None


def test_list_overdue_tasks(tmp_path) -> None:
    connection = _make_connection(tmp_path)
    player_id = _create_player(connection)

    from app.services.coach_tasks import create_coach_task, list_overdue_tasks

    create_coach_task(
        connection=connection,
        player_id=player_id,
        title="Overdue task",
        due_date="2020-01-01",
    )
    create_coach_task(
        connection=connection,
        player_id=player_id,
        title="Future task",
        due_date="2099-12-31",
    )

    overdue = list_overdue_tasks(connection=connection)
    assert len(overdue) == 1
    assert overdue[0].title == "Overdue task"


def test_delete_coach_task(tmp_path) -> None:
    connection = _make_connection(tmp_path)
    player_id = _create_player(connection)

    from app.services.coach_tasks import create_coach_task, delete_coach_task, get_coach_task

    task_id = create_coach_task(connection=connection, player_id=player_id, title="To delete")
    delete_coach_task(connection=connection, task_id=task_id)

    task = get_coach_task(connection=connection, task_id=task_id)
    assert task is None

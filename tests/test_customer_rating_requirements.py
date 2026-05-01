from __future__ import annotations

import pytest
from inspect import signature

from app.db.database import get_connection
from app.db.repositories import ResultRepository
from app.domain.points import points_for_place
from app.services.batch_export import BatchExportService
from app.services.import_review import build_import_rating_preview
from app.services.manual_tournament import create_manual_adult_tournament
from app.services.rating_snapshot import list_rating_snapshot_rows, list_rating_snapshot_sessions
from app.services.rating_snapshot import create_rating_snapshot_for_tournament_publish
from app.services.recalculate_tournament import recalculate_tournament_results
from app.services.tournament_lifecycle import transition_tournament_status
from app.ui.labels import adult_scope_label, category_label


@pytest.mark.parametrize(
    ("place", "expected_points"),
    [
        (1, 14),
        (2, 12),
        (3, 10),
        (4, 10),
        (5, 8),
        (8, 8),
        (9, 6),
        (16, 6),
        (17, 4),
        (32, 4),
        (33, 2),
        (64, 2),
        (65, 0),
    ],
)
def test_customer_place_points_table(place: int, expected_points: int) -> None:
    assert points_for_place(place) == expected_points


def test_customer_rating_default_n_is_three() -> None:
    assert signature(BatchExportService.export_all).parameters["n_value"].default == 3
    assert signature(build_import_rating_preview).parameters["n_value"].default == 3
    assert signature(create_rating_snapshot_for_tournament_publish).parameters["n_value"].default == 3


def test_customer_category_and_adult_scope_labels_are_complete() -> None:
    assert category_label("U10-M") == "Юноши до 10 лет"
    assert category_label("U10-W") == "Девушки до 10 лет"
    assert category_label("U12-M") == "Юноши до 12 лет"
    assert category_label("U15-W") == "Девушки до 15 лет"
    assert category_label("JUNIOR-M") == "Юниоры"
    assert category_label("JUNIOR-W") == "Юниорки"
    assert adult_scope_label("overall") == "Все взрослые"
    assert adult_scope_label("men") == "Мужчины"
    assert adult_scope_label("women") == "Женщины"


def test_customer_adult_rating_scopes_keep_manual_points_without_classification(tmp_path) -> None:
    connection = get_connection(tmp_path / "customer-adult-rating.db")

    report = create_manual_adult_tournament(
        connection=connection,
        tournament_name="Взрослый контрольный турнир",
        tournament_date="2026-04-30",
        league_code=None,
        rows=[
            {
                "fio": "Иванов Иван",
                "birth": "1988-01-01",
                "gender": "мужской",
                "place": 1,
                "points_total": 140,
            },
            {
                "fio": "Петрова Анна",
                "birth": "1990-02-02",
                "gender": "женский",
                "place": 2,
                "points_total": 125,
            },
            {
                "fio": "Смирнов Алекс",
                "birth": "1991-03-03",
                "place": 3,
                "points_total": 111,
            },
        ],
        operation_group_id="op-customer-adult-rating",
    )

    recalc = recalculate_tournament_results(
        connection=connection,
        tournament_id=report.tournament_id,
    )
    assert recalc.results_updated == 3

    for target_status in ("review", "confirmed", "published"):
        result = transition_tournament_status(
            connection=connection,
            tournament_id=report.tournament_id,
            to_status=target_status,
            context={"actor": "tests", "operation_group_id": "op-customer-adult-rating"},
        )
        assert result["ok"] is True

    result_rows = ResultRepository(connection).list_with_players(report.tournament_id)
    assert [
        (row["place"], row["points_total"], row["points_classification"], row["calc_version"])
        for row in result_rows
    ] == [
        (1, 140, 0, "manual_adult_v1"),
        (2, 125, 0, "manual_adult_v1"),
        (3, 111, 0, "manual_adult_v1"),
    ]

    overall_sessions = list_rating_snapshot_sessions(connection, scope_type="adult", scope_key="overall")
    men_sessions = list_rating_snapshot_sessions(connection, scope_type="adult", scope_key="men")
    women_sessions = list_rating_snapshot_sessions(connection, scope_type="adult", scope_key="women")

    assert len(overall_sessions) == 1
    assert len(men_sessions) == 1
    assert len(women_sessions) == 1

    overall_rows = list_rating_snapshot_rows(
        connection,
        snapshot_created_at=overall_sessions[0].created_at,
        scope_type="adult",
        scope_key="overall",
    )
    men_rows = list_rating_snapshot_rows(
        connection,
        snapshot_created_at=men_sessions[0].created_at,
        scope_type="adult",
        scope_key="men",
    )
    women_rows = list_rating_snapshot_rows(
        connection,
        snapshot_created_at=women_sessions[0].created_at,
        scope_type="adult",
        scope_key="women",
    )

    assert [(row.position, row.fio, row.points) for row in overall_rows] == [
        (1, "Иванов Иван", 140),
        (2, "Петрова Анна", 125),
        (3, "Смирнов Алекс", 111),
    ]
    assert [(row.position, row.fio, row.points) for row in men_rows] == [(1, "Иванов Иван", 140)]
    assert [(row.position, row.fio, row.points) for row in women_rows] == [(1, "Петрова Анна", 125)]

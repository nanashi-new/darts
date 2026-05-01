from __future__ import annotations

import os
import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from app.db.database import get_connection
from app.db.repositories import ResultRepository, TournamentRepository
from app.services.import_xlsx import (
    import_tournament_table_blocks,
    parse_first_table_from_xlsx_with_report,
    parse_tables_from_xlsx_with_report,
)

from tests.helpers.xlsx_factory import make_multi_table_xlsx, make_single_table_xlsx


def _workspace_tmp_path() -> Path:
    path = Path(".tmp") / f"customer-import-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def test_customer_import_requires_birth_and_all_exercise_columns() -> None:
    tmp_path = _workspace_tmp_path()
    path = make_single_table_xlsx(
        tmp_path,
        headers=["ФИО", "Место", "Набор очков"],
        rows=[["Иванов Иван", 1, 120]],
    )

    try:
        report = parse_first_table_from_xlsx_with_report(str(path))
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)

    assert report.needs_mapping is True
    assert report.confidence < 1.0
    assert report.missing_required_columns == [
        "Дата рождения",
        "Сектор 20",
        "Большой раунд",
    ]


def test_customer_import_aliases_cover_required_columns_case_insensitively() -> None:
    tmp_path = _workspace_tmp_path()
    path = make_single_table_xlsx(
        tmp_path,
        headers=["игрок", "ДАТА РОЖДЕНИЯ", "позиция", "результат", "20", "BR"],
        rows=[["Иванов Иван", "2012-01-02", 1, 120, 45, 78]],
    )

    try:
        report = parse_first_table_from_xlsx_with_report(str(path))
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)

    assert report.needs_mapping is False
    assert report.missing_required_columns == []
    row = report.rows[0]
    assert row["fio"] == "Иванов Иван"
    assert row["birth"] == "2012-01-02"
    assert row["place"] == 1
    assert row["score_set"] == 120
    assert row["score_sector20"] == 45
    assert row["score_big_round"] == 78


def test_customer_mapping_dialog_requires_birth_and_all_exercise_columns() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication

        from app.ui.column_mapping_dialog import ColumnMappingDialog
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Qt mapping dialog smoke unavailable: {exc}")

    app = QApplication.instance() or QApplication([])
    _ = app
    dialog = ColumnMappingDialog(
        headers=["ФИО", "Место", "Очки"],
        preview_rows=[["Иванов Иван", 1, 120]],
    )

    assert dialog.ok_button.isEnabled() is False
    status = dialog.status_label.text()
    assert "Дата рождения или год рождения" in status
    assert "Сектор 20" in status
    assert "Большой раунд" in status


def test_customer_import_applies_all_selected_xlsx_tables_as_one_draft_tournament() -> None:
    tmp_path = _workspace_tmp_path()
    path = make_multi_table_xlsx(
        tmp_path,
        blocks=[
            {
                "title": "Группа 1",
                "headers": ["ФИО", "Дата рождения", "Место", "Набор очков", "Сектор 20", "Большой раунд"],
                "rows": [
                    ["Иванов Иван", "2012-01-02", 1, 120, 45, 78],
                    ["Петров Петр", "2012-02-03", 2, 100, 38, 70],
                ],
            },
            {
                "title": "Группа 2",
                "headers": ["ФИО", "Дата рождения", "Место", "Набор очков", "Сектор 20", "Большой раунд"],
                "rows": [
                    ["Сидоров Семен", "2012-03-04", 3, 95, 35, 66],
                ],
            },
        ],
    )
    connection = get_connection(tmp_path / "multi-table-import.db")

    try:
        blocks = parse_tables_from_xlsx_with_report(str(path))
        report = import_tournament_table_blocks(
            connection=connection,
            blocks=blocks,
            tournament_name="Многотабличный кубок",
            tournament_date="2026-04-30",
            category_code="U12",
            source_files=[str(path)],
            operation_group_id="op-customer-multi-table",
        )
        tournament = TournamentRepository(connection).get(report.tournament_id)
        results = ResultRepository(connection).list_with_players(report.tournament_id)
    finally:
        connection.close()
        shutil.rmtree(tmp_path, ignore_errors=True)

    assert len(blocks) == 2
    assert report.tournament_status == "draft"
    assert report.has_draft_changes is True
    assert report.tables_processed == 2
    assert report.rows_read == 3
    assert report.imported_rows == 3
    assert tournament is not None
    assert tournament["status"] == "draft"
    assert [row["points_total"] for row in results] == [14, 12, 10]

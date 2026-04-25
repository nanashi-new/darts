from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.db.database import get_connection
from app.db.repositories import PlayerRepository
from app.services.audit_log import IMPORT_REPORT
from app.services.import_xlsx import ImportApplyReport, import_tournament_rows
from app.services.tournament_lifecycle import transition_tournament_status


def _create_player(
    player_repo: PlayerRepository,
    *,
    last_name: str,
    first_name: str,
    birth_date: str | None,
) -> int:
    return player_repo.create(
        {
            "last_name": last_name,
            "first_name": first_name,
            "middle_name": None,
            "birth_date": birth_date,
            "gender": None,
            "coach": None,
            "club": None,
            "notes": None,
        }
    )


@pytest.mark.unit
def test_build_import_session_report_and_renderers_include_required_fields() -> None:
    from app.services.import_report import (
        ImportSessionReport,
        render_import_report_json,
        render_import_report_text,
    )

    report = ImportSessionReport(
        operation_group_id="op-import-1",
        tournament_id=42,
        tournament_name="Spring Cup",
        category_code="U14",
        tournament_status="published",
        apply_status="published",
        files_processed=1,
        tables_processed=1,
        rows_read=3,
        rows_imported=2,
        rows_skipped=1,
        players_created=1,
        players_reused=1,
        players_matched_manually=1,
        warnings=["Нужна ручная проверка"],
        warnings_count=1,
        errors_count=0,
        source_files=["/tmp/import.xlsx"],
    )

    text_report = render_import_report_text(report)
    json_payload = json.loads(render_import_report_json(report))

    assert "Spring Cup" in text_report
    assert "Обработано файлов: 1" in text_report
    assert "Обработано таблиц: 1" in text_report
    assert "Прочитано строк: 3" in text_report
    assert "Импортировано строк: 2" in text_report
    assert "Пропущено строк: 1" in text_report
    assert "Создано игроков: 1" in text_report
    assert "Переиспользовано игроков: 1" in text_report
    assert "Сопоставлено вручную: 1" in text_report
    assert json_payload["operation_group_id"] == "op-import-1"
    assert json_payload["apply_status"] == "published"
    assert json_payload["warnings"] == ["Нужна ручная проверка"]
    assert json_payload["source_files"] == ["/tmp/import.xlsx"]


@pytest.mark.integration
def test_import_apply_report_counts_created_reused_and_manual_matches(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "import-report-counts.db")
    players = PlayerRepository(connection)

    reused_player_id = _create_player(
        players,
        last_name="reused",
        first_name="one",
        birth_date="2011-05-01",
    )
    manual_first_id = _create_player(
        players,
        last_name="manual",
        first_name="choice",
        birth_date="2012-03-01",
    )
    _create_player(
        players,
        last_name="manual",
        first_name="choice",
        birth_date="2012-07-01",
    )

    def resolver(
        fio: str,
        birth_date_or_year: str | None,
        candidates: list[dict[str, object]],
    ) -> dict[str, object]:
        assert fio == "Manual Choice"
        assert birth_date_or_year == "2012"
        assert len(candidates) == 2
        return {"action": "select", "player_id": manual_first_id, "remember": False}

    apply_report = import_tournament_rows(
        connection=connection,
        rows=[
            {
                "fio": "Reused One",
                "birth": "2011-05-01",
                "place": 1,
                "score_set": 50,
                "score_sector20": 10,
                "score_big_round": 10,
            },
            {
                "fio": "Manual Choice",
                "birth": "2012",
                "place": 2,
                "score_set": 40,
                "score_sector20": 9,
                "score_big_round": 9,
            },
            {
                "fio": "New Person",
                "birth": "2013-01-01",
                "place": 3,
                "score_set": 30,
                "score_sector20": 8,
                "score_big_round": 8,
            },
        ],
        tournament_name="Metrics Cup",
        tournament_date="2026-04-01",
        category_code="U14",
        source_files=["/tmp/import.xlsx"],
        player_match_resolver=resolver,
        operation_group_id="op-import-counts",
    )

    assert apply_report.operation_group_id == "op-import-counts"
    assert apply_report.files_processed == 1
    assert apply_report.tables_processed == 1
    assert apply_report.rows_read == 3
    assert apply_report.imported_rows == 3
    assert apply_report.skipped_rows == 0
    assert apply_report.players_created == 1
    assert apply_report.players_reused == 2
    assert apply_report.players_matched_manually == 1
    assert reused_player_id > 0


@pytest.mark.integration
def test_persisted_import_report_links_to_lifecycle_operation_group(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "import-report-persist.db")

    apply_report = import_tournament_rows(
        connection=connection,
        rows=[
            {
                "fio": "Ivanov Ivan",
                "birth": "2010-01-01",
                "place": 1,
                "score_set": 60,
                "score_sector20": 20,
                "score_big_round": 10,
            }
        ],
        tournament_name="Persisted Cup",
        tournament_date="2026-04-05",
        category_code="U14",
        source_files=["/tmp/imported.xlsx"],
        operation_group_id="op-import-persisted",
    )

    from app.services.import_report import (
        build_import_session_report,
        list_import_reports,
        persist_import_session_report,
    )

    draft_report = build_import_session_report(
        connection=connection,
        apply_report=apply_report,
        apply_status="draft_applied",
    )
    persist_import_session_report(connection=connection, report=draft_report)

    draft_events = connection.execute(
        """
        SELECT event_type, operation_group_id, context_json
        FROM audit_log
        WHERE event_type = ?
        ORDER BY id ASC
        """,
        (IMPORT_REPORT,),
    ).fetchall()
    assert len(draft_events) == 1
    assert draft_events[0]["operation_group_id"] == "op-import-persisted"
    assert json.loads(str(draft_events[0]["context_json"]))["apply_status"] == "draft_applied"

    assert transition_tournament_status(
        connection=connection,
        tournament_id=apply_report.tournament_id,
        to_status="review",
        context={"actor": "tests", "operation_group_id": apply_report.operation_group_id},
    )["ok"] is True
    assert transition_tournament_status(
        connection=connection,
        tournament_id=apply_report.tournament_id,
        to_status="confirmed",
        context={"actor": "tests", "operation_group_id": apply_report.operation_group_id},
    )["ok"] is True
    assert transition_tournament_status(
        connection=connection,
        tournament_id=apply_report.tournament_id,
        to_status="published",
        context={"actor": "tests", "operation_group_id": apply_report.operation_group_id},
    )["ok"] is True

    published_report = build_import_session_report(
        connection=connection,
        apply_report=apply_report,
        apply_status="published",
    )
    persist_import_session_report(connection=connection, report=published_report)

    records = list_import_reports(connection)
    assert len(records) == 2
    assert records[0].report.apply_status == "published"
    assert records[0].report.operation_group_id == "op-import-persisted"
    assert records[1].report.apply_status == "draft_applied"

    lifecycle_events = connection.execute(
        """
        SELECT event_type, operation_group_id
        FROM audit_log
        WHERE entity_type = 'tournament'
          AND entity_id = ?
          AND event_type IN ('tournament_updated', 'tournament_published')
        ORDER BY id ASC
        """,
        (str(apply_report.tournament_id),),
    ).fetchall()
    assert len(lifecycle_events) == 3
    assert {row["operation_group_id"] for row in lifecycle_events} == {"op-import-persisted"}

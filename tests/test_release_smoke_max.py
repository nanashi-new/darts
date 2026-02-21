from __future__ import annotations

from pathlib import Path

import pytest
from openpyxl import Workbook

from app.db.database import get_connection
from app.db.repositories import ResultRepository
from app.services.audit_log import AuditLogService, EXPORT_FILE, IMPORT_FILE
from app.services.export_service import ExportService
from app.services.import_xlsx import import_tournament_results
from app.services.recalculate_rating import RecalculateRatingService

pytestmark = pytest.mark.release_smoke


def _is_expected_headless_qt_failure(exc: Exception) -> bool:
    message = str(exc).lower()
    markers = (
        "libgl.so.1",
        "libegl.so.1",
        "could not load the qt platform plugin",
        "no qt platform plugin could be initialized",
        "qt.qpa.plugin",
        "xcb",
        "offscreen",
    )
    return isinstance(exc, (ImportError, OSError, RuntimeError)) and any(marker in message for marker in markers)

def _create_import_file(path: Path) -> Path:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Results"
    sheet.append(["ФИО", "Год рождения", "Место", "Очки", "С20", "БР"])
    sheet.append(["Иванов Иван", 2010, 1, 120, 45, 30])
    sheet.append(["Петров Петр", 2011, 2, 100, 40, 25])
    workbook.save(path)
    return path


def test_release_smoke_critical_path(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "app.db")
    result_repo = ResultRepository(connection)

    import_file = _create_import_file(tmp_path / "import.xlsx")
    tournament_id, _ = import_tournament_results(
        connection=connection,
        file_path=str(import_file),
        tournament_name="Release E2E",
        tournament_date="2025-01-15",
        category_code="U12-M",
    )

    imported_results = result_repo.search(tournament_id=tournament_id)
    assert len(imported_results) == 2

    recalc_service = RecalculateRatingService()
    single_report = recalc_service.run(connection=connection, tournament_id=tournament_id)
    all_report = recalc_service.run(connection=connection)

    assert single_report.tournaments_processed == 1
    assert single_report.results_updated == 2
    assert single_report.errors == []
    assert all_report.tournaments_processed >= 1
    assert all_report.results_updated >= 2
    assert all_report.errors == []

    exporter = ExportService()
    rows = [["1", "Иванов Иван", "120"], ["2", "Петров Петр", "100"]]

    xlsx_path = tmp_path / "rating.xlsx"
    exporter.export_dataset_xlsx(
        str(xlsx_path),
        header_lines=["Release smoke"],
        columns=["Место", "ФИО", "Очки"],
        rows=rows,
    )
    assert xlsx_path.exists()
    assert xlsx_path.stat().st_size > 0

    pdf_path = tmp_path / "rating.pdf"
    exporter.export_dataset_pdf(
        str(pdf_path),
        header_lines=["Release smoke"],
        columns=["Место", "ФИО", "Очки"],
        rows=rows,
    )
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0

    png_path = tmp_path / "rating.png"
    try:
        exporter.export_dataset_image(
            str(png_path),
            columns=["Место", "ФИО", "Очки"],
            rows=rows,
            column_widths=[100, 220, 120],
        )
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless PNG export unavailable: {exc}")
        raise
    assert png_path.exists()
    assert png_path.stat().st_size > 0

    audit = AuditLogService(connection)
    audit.log_event(IMPORT_FILE, "Импорт", "import.xlsx")
    audit.log_event(EXPORT_FILE, "Экспорт", "rating.pdf")

    events = audit.list_events()
    export_events = audit.list_events(event_type=EXPORT_FILE)

    assert len(events) == 2
    assert len(export_events) == 1
    assert export_events[0].details == "rating.pdf"

    audit_path = audit.export_txt(tmp_path / "audit.txt")
    content = audit_path.read_text(encoding="utf-8")

    assert audit_path.exists()
    assert audit_path.stat().st_size > 0
    assert "Traceback" not in content

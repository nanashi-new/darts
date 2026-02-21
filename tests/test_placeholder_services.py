from __future__ import annotations

from pathlib import Path

from app.db.database import get_connection
from app.services.export_pdf import ExportPdfService
from app.services.export_xlsx import ExportXlsxService
from app.services.recalculate_rating import RecalculateRatingService


def test_export_wrappers_create_files(tmp_path: Path) -> None:
    rows = [["1", "Иванов Иван", "20"]]
    columns = ["Место", "ФИО", "Очки"]
    header = ["Рейтинг", "Дата: 2026-01-01"]

    pdf_path = tmp_path / "rating.pdf"
    xlsx_path = tmp_path / "rating.xlsx"

    ExportPdfService().run(
        path=str(pdf_path),
        header_lines=header,
        columns=columns,
        rows=rows,
    )
    ExportXlsxService().run(
        path=str(xlsx_path),
        header_lines=header,
        columns=columns,
        rows=rows,
    )

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0
    assert xlsx_path.exists()
    assert xlsx_path.stat().st_size > 0


def test_recalculate_rating_service_runs_on_empty_db(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "empty.db")
    try:
        report = RecalculateRatingService().run(connection=connection)
    finally:
        connection.close()

    assert report.tournaments_processed == 0
    assert report.results_updated == 0
    assert report.errors == []

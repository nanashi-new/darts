from __future__ import annotations

import pytest

from app.services.export_pdf import ExportPdfService
from app.services.export_xlsx import ExportXlsxService
from app.services.recalculate_rating import RecalculateRatingService
from app.services.recalculate_tournament import RecalculationReport



pytestmark = [pytest.mark.integration, pytest.mark.legacy]

def test_recalculate_rating_service_runs_targeted(monkeypatch: pytest.MonkeyPatch) -> None:
    report = RecalculationReport(tournaments_processed=1, results_updated=2)

    def fake_recalculate_tournament_results(*, connection, tournament_id: int) -> RecalculationReport:
        assert connection == "db"
        assert tournament_id == 10
        return report

    monkeypatch.setattr(
        "app.services.recalculate_rating.recalculate_tournament_results",
        fake_recalculate_tournament_results,
    )

    service = RecalculateRatingService()
    result = service.run(connection="db", tournament_id=10)

    assert result is report


def test_recalculate_rating_service_runs_all(monkeypatch: pytest.MonkeyPatch) -> None:
    report = RecalculationReport(tournaments_processed=3, results_updated=5)

    def fake_recalculate_all_tournaments(*, connection) -> RecalculationReport:
        assert connection == "db"
        return report

    monkeypatch.setattr(
        "app.services.recalculate_rating.recalculate_all_tournaments",
        fake_recalculate_all_tournaments,
    )

    service = RecalculateRatingService()
    result = service.run(connection="db")

    assert result is report


def test_recalculate_rating_service_validates_inputs() -> None:
    service = RecalculateRatingService()

    with pytest.raises(ValueError, match="connection is required"):
        service.run(connection=None)

    with pytest.raises(ValueError, match="tournament_id must be a positive integer"):
        service.run(connection="db", tournament_id=0)


def test_export_pdf_service_delegates() -> None:
    calls: dict[str, object] = {}

    class FakeExportService:
        def export_dataset_pdf(self, *, path, header_lines, columns, rows, column_widths=None) -> None:
            calls["path"] = path
            calls["header_lines"] = list(header_lines)
            calls["columns"] = list(columns)
            calls["rows"] = [list(row) for row in rows]
            calls["column_widths"] = column_widths

    service = ExportPdfService(export_service=FakeExportService())
    service.run(
        path="/tmp/file.pdf",
        header_lines=["Title"],
        columns=["A"],
        rows=[["1"]],
        column_widths=[100],
    )

    assert calls["path"] == "/tmp/file.pdf"
    assert calls["columns"] == ["A"]


def test_export_pdf_service_validates_inputs() -> None:
    service = ExportPdfService()

    with pytest.raises(ValueError, match="path is required"):
        service.run(path="", header_lines=[], columns=["A"], rows=[])

    with pytest.raises(ValueError, match="columns must not be empty"):
        service.run(path="/tmp/file.pdf", header_lines=[], columns=[], rows=[])


def test_export_xlsx_service_delegates() -> None:
    calls: dict[str, object] = {}

    class FakeExportService:
        def export_dataset_xlsx(self, *, path, header_lines, columns, rows) -> None:
            calls["path"] = path
            calls["header_lines"] = list(header_lines)
            calls["columns"] = list(columns)
            calls["rows"] = [list(row) for row in rows]

    service = ExportXlsxService(export_service=FakeExportService())
    service.run(
        path="/tmp/file.xlsx",
        header_lines=["Title"],
        columns=["A"],
        rows=[["1"]],
    )

    assert calls["path"] == "/tmp/file.xlsx"
    assert calls["columns"] == ["A"]


def test_export_xlsx_service_validates_inputs() -> None:
    service = ExportXlsxService()

    with pytest.raises(ValueError, match="path is required"):
        service.run(path="", header_lines=[], columns=["A"], rows=[])

    with pytest.raises(ValueError, match="columns must not be empty"):
        service.run(path="/tmp/file.xlsx", header_lines=[], columns=[], rows=[])

from __future__ import annotations

from typing import Iterable, Sequence

from app.services.export_service import ExportService


class ExportPdfService:
    """Backwards-compatible façade for PDF export."""

    def __init__(self, export_service: ExportService | None = None) -> None:
        self._export_service = export_service or ExportService()

    def run(
        self,
        *,
        path: str,
        header_lines: Iterable[str],
        columns: Sequence[str],
        rows: Sequence[Sequence[str]],
        column_widths: Sequence[int] | None = None,
    ) -> None:
        """Export tabular data to PDF.

        Raises:
            ValueError: If required arguments are empty.
        """
        if not path:
            raise ValueError("path is required")
        if not columns:
            raise ValueError("columns must not be empty")

        self._export_service.export_dataset_pdf(
            path=path,
            header_lines=header_lines,
            columns=columns,
            rows=rows,
            column_widths=column_widths,
        )

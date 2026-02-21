from __future__ import annotations

from os import PathLike
from typing import Iterable, Sequence

from app.services.export_service import ExportService


class ExportXlsxService:
    """Compatibility wrapper for XLSX export."""

    def __init__(self, export_service: ExportService | None = None) -> None:
        self._export_service = export_service or ExportService()

    def run(
        self,
        *,
        path: str | PathLike[str],
        header_lines: Iterable[str],
        columns: Sequence[str],
        rows: Sequence[Sequence[str]],
    ) -> None:
        normalized_path = str(path)
        if not normalized_path:
            raise ValueError("path is required")
        if not columns:
            raise ValueError("columns must not be empty")

        self._export_service.export_dataset_xlsx(
            path=normalized_path,
            header_lines=header_lines,
            columns=columns,
            rows=rows,
        )

    def export(
        self,
        *,
        path: str | PathLike[str],
        header_lines: Iterable[str],
        columns: Sequence[str],
        rows: Sequence[Sequence[str]],
    ) -> None:
        """Backwards-compatible alias for older integrations."""

        self.run(
            path=path,
            header_lines=header_lines,
            columns=columns,
            rows=rows,
        )

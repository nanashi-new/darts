from __future__ import annotations

from pathlib import Path

from app.services.import_clipboard import parse_tables_from_clipboard_text
from app.services.import_csv import parse_tables_from_csv
from app.services.import_json import parse_tables_from_json
from app.services.import_protocol_docx import parse_tables_from_docx
from app.services.import_protocol_pdf import parse_tables_from_pdf
from app.services.import_xlsx import TableBlock, parse_tables_from_xlsx_with_report


def detect_format(path: str) -> str:
    """Detect import file format by extension. Returns 'xlsx', 'csv', 'json', 'docx', or 'pdf'."""
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix == ".json":
        return "json"
    if suffix == ".docx":
        return "docx"
    if suffix == ".pdf":
        return "pdf"
    return "xlsx"


def parse_tables_from_file(path: str) -> list[TableBlock]:
    """Dispatch to correct parser based on file extension."""
    fmt = detect_format(path)
    if fmt == "csv":
        return parse_tables_from_csv(path)
    if fmt == "json":
        return parse_tables_from_json(path)
    if fmt == "docx":
        return parse_tables_from_docx(path)
    if fmt == "pdf":
        return parse_tables_from_pdf(path)
    return parse_tables_from_xlsx_with_report(path)


__all__ = [
    "detect_format",
    "parse_tables_from_clipboard_text",
    "parse_tables_from_file",
]

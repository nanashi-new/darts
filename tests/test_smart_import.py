from __future__ import annotations

import pytest
from docx import Document

from app.services.import_protocol_docx import parse_tables_from_docx

pytestmark = pytest.mark.integration


def _add_classification_table(doc: Document, rows_data: list[list[str]]) -> None:
    """Add a classification-style table (16 columns) to a document."""
    headers = [
        "место", "ФИО", "", "", "Г/Р",
        "тренер", "", "", "набор очков", "",
        "сектор 20", "", "Большой раунд", "", "итого",
        "выполненный разряд",
    ]
    num_cols = len(headers)
    table = doc.add_table(rows=1 + len(rows_data), cols=num_cols)
    # Set header row
    for i, h in enumerate(headers):
        table.rows[0].cells[i].text = h
    # Set data rows
    for row_idx, row in enumerate(rows_data, start=1):
        for col_idx, val in enumerate(row):
            if col_idx < num_cols:
                table.rows[row_idx].cells[col_idx].text = val


def _add_501_table(doc: Document, rows_data: list[list[str]]) -> None:
    """Add a 501-style table (7 columns) to a document."""
    headers = [
        "МЕСТО", "Фамилия, Имя", "Год рождения",
        "Звание, разряд", "Субъект РФ, город", "тренер", "Выполнен разряд",
    ]
    num_cols = len(headers)
    table = doc.add_table(rows=1 + len(rows_data), cols=num_cols)
    for i, h in enumerate(headers):
        table.rows[0].cells[i].text = h
    for row_idx, row in enumerate(rows_data, start=1):
        for col_idx, val in enumerate(row):
            if col_idx < num_cols:
                table.rows[row_idx].cells[col_idx].text = val


def _add_jury_table(doc: Document) -> None:
    """Add a 4-column jury table to a document."""
    headers = ["должность", "ФИО", "город", "формат"]
    table = doc.add_table(rows=2, cols=4)
    for i, h in enumerate(headers):
        table.rows[0].cells[i].text = h
    table.rows[1].cells[0].text = "Главный судья"
    table.rows[1].cells[1].text = "Иванов И.И."
    table.rows[1].cells[2].text = "Москва"
    table.rows[1].cells[3].text = "501"


def test_parse_docx_classification_table(tmp_path) -> None:
    """Classification table with 2 data rows should produce 1 TableBlock."""
    doc = Document()
    doc.add_paragraph("Юниоры 15-17 лет")

    rows_data = [
        ["1", "Иванов Иван", "", "", "2008", "Петров П.П.", "", "", "150", "", "80", "", "60", "", "290", "1р"],
        ["2", "Сидоров Сидор", "", "", "2009", "Козлов К.К.", "", "", "130", "", "70", "", "50", "", "250", "2р"],
    ]
    _add_classification_table(doc, rows_data)

    path = tmp_path / "test_classification.docx"
    doc.save(str(path))

    result = parse_tables_from_docx(str(path))

    assert len(result) == 1
    block = result[0]
    assert block.sheet_name == "Юниоры 15-17 лет"
    assert len(block.rows) == 2
    assert block.rows[0]["fio"] == "Иванов Иван"
    assert block.rows[0]["birth"] == "2008"
    assert block.rows[0]["coach"] == "Петров П.П."
    assert block.rows[0]["place"] == "1"
    assert block.rows[0]["score_set"] == "150"
    assert block.rows[0]["score_sector20"] == "80"
    assert block.rows[0]["score_big_round"] == "60"
    assert block.confidence == 1.0
    assert block.needs_mapping is False


def test_parse_docx_skips_jury_table(tmp_path) -> None:
    """Jury tables (4 cols with jury keywords) should be skipped."""
    doc = Document()
    doc.add_paragraph("Мужчины 18+ лет")

    _add_jury_table(doc)

    rows_data = [
        ["1", "Иванов Иван", "1990", "КМС", "Москва", "Тренеров Т.Т.", "КМС"],
    ]
    _add_501_table(doc, rows_data)

    path = tmp_path / "test_jury_skip.docx"
    doc.save(str(path))

    result = parse_tables_from_docx(str(path))

    assert len(result) == 1
    block = result[0]
    assert block.rows[0]["fio"] == "Иванов Иван"
    assert block.rows[0]["birth"] == "1990"
    assert block.rows[0]["coach"] == "Тренеров Т.Т."
    assert block.rows[0]["place"] == "1"


def test_parse_docx_empty_file(tmp_path) -> None:
    """An empty DOCX file should return empty list without raising."""
    doc = Document()
    path = tmp_path / "empty.docx"
    doc.save(str(path))

    result = parse_tables_from_docx(str(path))
    assert result == []


def test_parse_docx_nonexistent_file() -> None:
    """A non-existent file should return empty list without raising."""
    result = parse_tables_from_docx("/nonexistent/path/file.docx")
    assert result == []


def test_parse_docx_501_table(tmp_path) -> None:
    """501-format table should be parsed with fio, birth, coach, place."""
    doc = Document()
    doc.add_paragraph("Женщины 18+ лет")

    rows_data = [
        ["1", "Петрова Мария", "1995", "1р", "СПб", "Сидоров С.С.", "КМС"],
        ["2", "Козлова Анна", "1998", "2р", "Москва", "Иванов И.И.", "1р"],
    ]
    _add_501_table(doc, rows_data)

    path = tmp_path / "test_501.docx"
    doc.save(str(path))

    result = parse_tables_from_docx(str(path))

    assert len(result) == 1
    block = result[0]
    assert block.sheet_name == "Женщины 18+ лет"
    assert len(block.rows) == 2
    assert block.rows[0]["fio"] == "Петрова Мария"
    assert block.rows[0]["birth"] == "1995"
    assert block.rows[0]["coach"] == "Сидоров С.С."
    assert block.rows[1]["fio"] == "Козлова Анна"
    # 501 tables don't have score columns
    assert block.rows[0]["score_set"] is None


def test_parse_docx_multiple_categories(tmp_path) -> None:
    """Multiple categories produce separate TableBlocks."""
    doc = Document()

    doc.add_paragraph("Юниоры 15-17 лет")
    _add_501_table(doc, [["1", "Иванов Иван", "2008", "", "", "Тренер А", ""]])

    doc.add_paragraph("Юниорки 15-17 лет")
    _add_501_table(doc, [["1", "Петрова Мария", "2009", "", "", "Тренер Б", ""]])

    path = tmp_path / "test_multi.docx"
    doc.save(str(path))

    result = parse_tables_from_docx(str(path))

    assert len(result) == 2
    assert result[0].sheet_name == "Юниоры 15-17 лет"
    assert result[1].sheet_name == "Юниорки 15-17 лет"

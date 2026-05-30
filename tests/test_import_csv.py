from __future__ import annotations

from pathlib import Path

from app.services.import_csv import parse_tables_from_csv


def _write_csv(tmp_path: Path, content: str, filename: str = "data.csv") -> str:
    file = tmp_path / filename
    file.write_text(content, encoding="utf-8")
    return str(file)


def test_comma_delimiter(tmp_path: Path) -> None:
    csv_content = "ФИО,Место,Набор,С20,БР\nИванов Иван,1,100,50,30\nПетров Петр,2,90,40,25\n"
    path = _write_csv(tmp_path, csv_content)
    blocks = parse_tables_from_csv(path)
    assert len(blocks) == 1
    block = blocks[0]
    assert len(block.rows) == 2
    assert block.rows[0]["fio"] == "Иванов Иван"
    assert block.rows[0]["place"] == "1"
    assert block.rows[0]["score_set"] == "100"


def test_semicolon_delimiter(tmp_path: Path) -> None:
    csv_content = "ФИО;Место;Набор;С20;БР\nИванов Иван;1;100;50;30\nПетров Петр;2;90;40;25\n"
    path = _write_csv(tmp_path, csv_content)
    blocks = parse_tables_from_csv(path)
    assert len(blocks) == 1
    block = blocks[0]
    assert len(block.rows) == 2
    assert block.rows[0]["fio"] == "Иванов Иван"
    assert block.rows[0]["place"] == "1"


def test_tab_delimiter(tmp_path: Path) -> None:
    csv_content = "ФИО\tМесто\tНабор\tС20\tБР\nИванов Иван\t1\t100\t50\t30\n"
    path = _write_csv(tmp_path, csv_content)
    blocks = parse_tables_from_csv(path)
    assert len(blocks) == 1
    block = blocks[0]
    assert len(block.rows) == 1
    assert block.rows[0]["fio"] == "Иванов Иван"
    assert block.rows[0]["score_big_round"] == "30"


def test_header_detection(tmp_path: Path) -> None:
    csv_content = "ФИО,Место,Набор,С20,БР\nИванов Иван,1,100,50,30\n"
    path = _write_csv(tmp_path, csv_content)
    blocks = parse_tables_from_csv(path)
    assert len(blocks) == 1
    block = blocks[0]
    assert block.sheet_name == "csv"
    assert "fio" in {v for v in block.header_mapping.values()}


def test_empty_file_returns_empty_list(tmp_path: Path) -> None:
    path = _write_csv(tmp_path, "")
    blocks = parse_tables_from_csv(path)
    assert blocks == []


def test_utf8_bom_handling(tmp_path: Path) -> None:
    csv_content = "ФИО,Место,Набор,С20,БР\nИванов Иван,1,100,50,30\n"
    file = tmp_path / "bom.csv"
    file.write_bytes(b"\xef\xbb\xbf" + csv_content.encode("utf-8"))
    blocks = parse_tables_from_csv(str(file))
    assert len(blocks) == 1
    block = blocks[0]
    assert len(block.rows) == 1
    assert block.rows[0]["fio"] == "Иванов Иван"


def test_nonexistent_file_returns_empty_list() -> None:
    blocks = parse_tables_from_csv("/nonexistent/path.csv")
    assert blocks == []


def test_no_valid_headers_returns_empty(tmp_path: Path) -> None:
    csv_content = "A,B,C\n1,2,3\n"
    path = _write_csv(tmp_path, csv_content)
    blocks = parse_tables_from_csv(path)
    assert blocks == []

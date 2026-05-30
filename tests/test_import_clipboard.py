from __future__ import annotations

from app.services.import_clipboard import parse_tables_from_clipboard_text


def test_tab_separated_text_parsing() -> None:
    text = "ФИО\tМесто\tНабор\tС20\tБР\nИванов Иван\t1\t100\t50\t30\nПетров Петр\t2\t90\t40\t25\n"
    blocks = parse_tables_from_clipboard_text(text)
    assert len(blocks) == 1
    block = blocks[0]
    assert len(block.rows) == 2
    assert block.rows[0]["fio"] == "Иванов Иван"
    assert block.rows[0]["place"] == "1"
    assert block.rows[0]["score_set"] == "100"
    assert block.rows[1]["fio"] == "Петров Петр"
    assert block.sheet_name == "clipboard"


def test_header_detection_from_first_row() -> None:
    text = "ФИО\tМесто\tНабор\nИванов Иван\t1\t100\n"
    blocks = parse_tables_from_clipboard_text(text)
    assert len(blocks) == 1
    block = blocks[0]
    assert "fio" in {v for v in block.header_mapping.values()}
    assert block.rows[0]["fio"] == "Иванов Иван"


def test_empty_text_returns_empty_list() -> None:
    blocks = parse_tables_from_clipboard_text("")
    assert blocks == []


def test_whitespace_only_returns_empty() -> None:
    blocks = parse_tables_from_clipboard_text("   \n  \t  \n")
    assert blocks == []


def test_no_valid_headers_returns_empty() -> None:
    text = "A\tB\tC\n1\t2\t3\n"
    blocks = parse_tables_from_clipboard_text(text)
    assert blocks == []


def test_windows_line_endings() -> None:
    text = "ФИО\tМесто\tНабор\r\nИванов Иван\t1\t100\r\nПетров Петр\t2\t90\r\n"
    blocks = parse_tables_from_clipboard_text(text)
    assert len(blocks) == 1
    block = blocks[0]
    assert len(block.rows) == 2
    assert block.rows[0]["fio"] == "Иванов Иван"

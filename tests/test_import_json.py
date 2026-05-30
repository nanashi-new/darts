from __future__ import annotations

import json
from pathlib import Path

from app.services.import_json import parse_tables_from_json


def _write_json(tmp_path: Path, data: object, filename: str = "data.json") -> str:
    file = tmp_path / filename
    file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return str(file)


def test_valid_json_array_standard_fields(tmp_path: Path) -> None:
    data = [
        {"fio": "Иванов Иван", "place": 1, "score_set": 100, "score_sector20": 50, "score_big_round": 30},
        {"fio": "Петров Петр", "place": 2, "score_set": 90, "score_sector20": 40, "score_big_round": 25},
    ]
    path = _write_json(tmp_path, data)
    blocks = parse_tables_from_json(path)
    assert len(blocks) == 1
    block = blocks[0]
    assert len(block.rows) == 2
    assert block.rows[0]["fio"] == "Иванов Иван"
    assert block.rows[0]["place"] == 1
    assert block.rows[0]["score_set"] == 100
    assert block.sheet_name == "json"


def test_field_synonym_mapping_player(tmp_path: Path) -> None:
    data = [
        {"player": "Иванов Иван", "position": 1, "score": 100},
    ]
    path = _write_json(tmp_path, data)
    blocks = parse_tables_from_json(path)
    assert len(blocks) == 1
    block = blocks[0]
    assert block.rows[0]["fio"] == "Иванов Иван"
    assert block.rows[0]["place"] == 1
    assert block.rows[0]["score_set"] == 100


def test_field_synonym_mapping_russian(tmp_path: Path) -> None:
    data = [
        {"игрок": "Сидоров", "место": 3, "очки": 80, "сектор20": 45, "бр": 20},
    ]
    path = _write_json(tmp_path, data)
    blocks = parse_tables_from_json(path)
    assert len(blocks) == 1
    block = blocks[0]
    assert block.rows[0]["fio"] == "Сидоров"
    assert block.rows[0]["place"] == 3
    assert block.rows[0]["score_set"] == 80
    assert block.rows[0]["score_sector20"] == 45
    assert block.rows[0]["score_big_round"] == 20


def test_malformed_json_returns_empty(tmp_path: Path) -> None:
    file = tmp_path / "bad.json"
    file.write_text("{invalid json", encoding="utf-8")
    blocks = parse_tables_from_json(str(file))
    assert blocks == []


def test_empty_array_returns_empty(tmp_path: Path) -> None:
    path = _write_json(tmp_path, [])
    blocks = parse_tables_from_json(path)
    assert blocks == []


def test_nonexistent_file_returns_empty() -> None:
    blocks = parse_tables_from_json("/nonexistent/data.json")
    assert blocks == []


def test_non_array_json_returns_empty(tmp_path: Path) -> None:
    path = _write_json(tmp_path, {"fio": "test"})
    blocks = parse_tables_from_json(path)
    assert blocks == []


def test_no_recognizable_fields_returns_empty(tmp_path: Path) -> None:
    data = [{"unknown_field": "value", "another": 123}]
    path = _write_json(tmp_path, data)
    blocks = parse_tables_from_json(path)
    assert blocks == []

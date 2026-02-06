from __future__ import annotations

import random
from pathlib import Path

from openpyxl import Workbook


HEADER_VARIANTS = [
    ["ФИО", "Место", "Очки", "С20", "БР"],
    ["Игрок", "place", "score", "sector20", "biground"],
    ["Фамилия Имя", "Место", "Набор", "Сектор 20", "Большой раунд"],
    ["Участник", "позиция", "результат", "20", "BR"],
]


FIO_POOL = [
    "Иванов Иван",
    "Петров Пётр",
    "Сидоров Семён",
    "Ким Алексей",
    "Ли Никита",
]


def _write_valid_xlsx(path: Path, tables_per_file: int, rows_per_table: int) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Data"

    for table_index in range(tables_per_file):
        headers = random.choice(HEADER_VARIANTS[:3] + [HEADER_VARIANTS[0]])
        sheet.append([f"Таблица {table_index + 1}"])
        sheet.append(headers)

        for row_index in range(rows_per_table):
            place_value: object = row_index + 1
            score_value: object = random.randint(20, 180)
            if row_index % 17 == 0:
                score_value = "1.5"
            sheet.append(
                [
                    random.choice(FIO_POOL),
                    place_value,
                    score_value,
                    random.randint(0, 60),
                    random.randint(0, 100),
                ]
            )

        sheet.append([])

    workbook.save(path)


def make_stress_xlsx_folder(
    tmp_path: Path,
    files: int = 30,
    tables_per_file: int = 3,
    rows_per_table: int = 64,
) -> Path:
    folder = tmp_path / "stress_xlsx"
    folder.mkdir(parents=True, exist_ok=True)

    corrupted_count = 2 if files >= 6 else 1
    empty_count = max(1, files // 10)
    valid_count = max(files - corrupted_count - empty_count, 1)

    for index in range(valid_count):
        _write_valid_xlsx(folder / f"valid_{index:03d}.xlsx", tables_per_file, rows_per_table)

    for index in range(empty_count):
        workbook = Workbook()
        workbook.save(folder / f"empty_{index:03d}.xlsx")

    for index in range(corrupted_count):
        (folder / f"broken_{index:03d}.xlsx").write_text("this-is-not-a-real-xlsx", encoding="utf-8")

    return folder

from __future__ import annotations

import random
import string

from tests.helpers.xlsx_factory import make_single_table_xlsx
from app.services.import_xlsx import parse_first_table_from_xlsx_with_report, parse_tables_from_xlsx_with_report


def _rand_cell() -> object:
    pool = [None, "", "  ", random.randint(0, 200), random.uniform(0, 200)]
    if random.random() < 0.4:
        pool.append("".join(random.choice(string.ascii_letters + " абвгд") for _ in range(random.randint(0, 12))))
    return random.choice(pool)


def test_import_fuzz_light(tmp_path) -> None:
    for _ in range(30):
        headers = [_rand_cell() for _ in range(random.randint(3, 7))]
        rows = [[_rand_cell() for _ in range(len(headers))] for _ in range(random.randint(1, 12))]
        path = make_single_table_xlsx(tmp_path, headers=headers, rows=rows)

        report = parse_first_table_from_xlsx_with_report(str(path))
        blocks = parse_tables_from_xlsx_with_report(str(path))

        assert report is not None
        assert isinstance(report.errors, list)
        assert isinstance(report.warnings, list)
        assert isinstance(blocks, list)

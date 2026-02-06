from __future__ import annotations

import time

from app.services.import_xlsx import import_batch_from_folder
from tests.helpers.stress_factory import make_stress_xlsx_folder


def test_perf_import_batch_max(tmp_path) -> None:
    folder = make_stress_xlsx_folder(tmp_path, files=20, tables_per_file=2, rows_per_table=50)

    started = time.perf_counter()
    result = import_batch_from_folder(str(folder))
    duration = time.perf_counter() - started

    print("import_batch_duration_s=", round(duration, 4))
    assert result["success"] + result["error"] == len(result["items"])
    assert result["success"] >= 14
    assert duration < 10.0

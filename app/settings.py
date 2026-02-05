from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
NORMS_XLSX_PATH = os.environ.get(
    "NORMS_XLSX_PATH",
    str(BASE_DIR / "resources" / "norms.xlsx"),
)

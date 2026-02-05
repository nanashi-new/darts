from __future__ import annotations

import base64
from pathlib import Path
from app.domain.ranks import Norms, load_norms_from_xlsx
from app.settings import NORMS_XLSX_PATH


def _ensure_norms_file(path: Path) -> bool:
    if path.exists():
        return True
    base64_path = path.with_suffix(path.suffix + ".b64")
    if not base64_path.exists():
        return False
    try:
        data = base64.b64decode(base64_path.read_text(encoding="utf-8"))
        path.write_bytes(data)
    except (OSError, ValueError):
        return False
    return True


def load_norms_from_settings() -> tuple[Norms | None, bool]:
    path = Path(NORMS_XLSX_PATH)
    if not _ensure_norms_file(path):
        return None, False
    try:
        norms = load_norms_from_xlsx(str(path))
    except OSError:
        return None, False
    return norms, True

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook

from app.domain.ranks import Norms, load_norms_from_xlsx
from app.settings import BASE_DIR, get_norms_xlsx_path


@dataclass(frozen=True)
class NormsLoadResult:
    norms: Norms | None
    loaded: bool
    path: str
    warning: str | None = None
    version: str | None = None
    updated_at: str | None = None


def _ensure_norms_file(path: Path) -> bool:
    if path.exists():
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    base64_path = BASE_DIR / "resources" / "norms.xlsx.b64"
    if not base64_path.exists():
        return False
    try:
        data = base64.b64decode(base64_path.read_text(encoding="utf-8"))
        path.write_bytes(data)
    except (OSError, ValueError):
        return False
    return True


def _read_norms_metadata(path: Path) -> tuple[str | None, str | None]:
    try:
        workbook = load_workbook(str(path), read_only=True, data_only=True)
        properties = workbook.properties
        version = properties.version
        updated_at = properties.modified or properties.created
        workbook.close()
    except OSError:
        return None, None

    normalized_date = None
    if isinstance(updated_at, datetime):
        normalized_date = updated_at.strftime("%Y-%m-%d")
    return version, normalized_date


def load_norms_from_settings() -> NormsLoadResult:
    path = Path(get_norms_xlsx_path())
    if not _ensure_norms_file(path):
        return NormsLoadResult(
            norms=None,
            loaded=False,
            path=str(path),
            warning="Файл нормативов не найден или не удалось материализовать шаблон.",
        )
    try:
        norms = load_norms_from_xlsx(str(path))
    except Exception:  # noqa: BLE001
        return NormsLoadResult(
            norms=None,
            loaded=False,
            path=str(path),
            warning="Не удалось загрузить нормативы: файл повреждён или имеет неверный формат.",
        )
    version, updated_at = _read_norms_metadata(path)
    return NormsLoadResult(
        norms=norms,
        loaded=True,
        path=str(path),
        version=version,
        updated_at=updated_at,
    )

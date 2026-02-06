from __future__ import annotations

import json
import os
from pathlib import Path

from app.db.database import APP_DIR_NAME

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_NORMS_XLSX_PATH = str(BASE_DIR / "resources" / "norms.xlsx")


def _get_app_settings_path() -> Path:
    if os.name == "nt":
        base_dir = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        root = Path(base_dir) if base_dir else Path.home() / "AppData" / "Roaming"
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    app_dir = root / APP_DIR_NAME
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir / "settings.json"


def _read_settings() -> dict[str, object]:
    path = _get_app_settings_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if isinstance(data, dict):
        return data
    return {}


def _write_settings(data: dict[str, object]) -> None:
    path = _get_app_settings_path()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_norms_xlsx_path() -> str:
    env_path = os.environ.get("NORMS_XLSX_PATH")
    if env_path:
        return env_path
    return str(_read_settings().get("norms_xlsx_path") or DEFAULT_NORMS_XLSX_PATH)


def set_norms_xlsx_path(path: str) -> None:
    settings = _read_settings()
    settings["norms_xlsx_path"] = path
    _write_settings(settings)

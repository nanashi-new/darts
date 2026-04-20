from __future__ import annotations

import json
import os

from app.runtime_paths import get_runtime_paths


def get_settings_path():
    return get_runtime_paths().settings_path


def load_settings() -> dict[str, object]:
    path = get_settings_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_settings(data: dict[str, object]) -> None:
    path = get_settings_path()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def update_setting(key: str, value: object) -> None:
    settings = load_settings()
    settings[key] = value
    save_settings(settings)


def get_default_norms_xlsx_path() -> str:
    return str(get_runtime_paths().profile_root / "norms.xlsx")


def get_norms_xlsx_path() -> str:
    env_path = os.environ.get("NORMS_XLSX_PATH")
    if env_path:
        return env_path
    return str(load_settings().get("norms_xlsx_path") or get_default_norms_xlsx_path())


def set_norms_xlsx_path(path: str) -> None:
    update_setting("norms_xlsx_path", path)


def get_saved_views() -> dict[str, object]:
    value = load_settings().get("saved_views")
    return value if isinstance(value, dict) else {}


def set_saved_views(saved_views: dict[str, object]) -> None:
    update_setting("saved_views", saved_views)


def get_layout_state() -> dict[str, object]:
    value = load_settings().get("layout_state")
    return value if isinstance(value, dict) else {}


def set_layout_state(layout_state: dict[str, object]) -> None:
    update_setting("layout_state", layout_state)


def get_last_self_check() -> dict[str, object]:
    value = load_settings().get("last_self_check")
    return value if isinstance(value, dict) else {}


def set_last_self_check(report_payload: dict[str, object]) -> None:
    update_setting("last_self_check", report_payload)

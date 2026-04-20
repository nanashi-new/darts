from __future__ import annotations

from copy import deepcopy

from app.settings import load_settings, save_settings


UI_STATE_KEY = "ui_state"


def get_ui_state() -> dict[str, object]:
    settings = load_settings()
    value = settings.get(UI_STATE_KEY)
    return deepcopy(value) if isinstance(value, dict) else {}


def set_ui_state(ui_state: dict[str, object]) -> None:
    settings = load_settings()
    settings[UI_STATE_KEY] = deepcopy(ui_state)
    save_settings(settings)


def get_view_state(view_key: str) -> dict[str, object]:
    value = get_ui_state().get(view_key)
    return deepcopy(value) if isinstance(value, dict) else {}


def update_view_state(view_key: str, state: dict[str, object]) -> None:
    ui_state = get_ui_state()
    ui_state[view_key] = deepcopy(state)
    set_ui_state(ui_state)

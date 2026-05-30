from __future__ import annotations

from copy import deepcopy

from app.settings import load_settings, save_settings


UI_STATE_KEY = "ui_state"
SESSION_FILTERS_KEY = "session_filters"


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


def get_session_filters(view_key: str) -> dict[str, object]:
    """Return saved filter values for a view."""
    ui_state = get_ui_state()
    filters_store = ui_state.get(SESSION_FILTERS_KEY)
    if not isinstance(filters_store, dict):
        return {}
    value = filters_store.get(view_key)
    return deepcopy(value) if isinstance(value, dict) else {}


def set_session_filters(view_key: str, filters: dict[str, object]) -> None:
    """Persist filter values for a view."""
    ui_state = get_ui_state()
    filters_store = ui_state.get(SESSION_FILTERS_KEY)
    if not isinstance(filters_store, dict):
        filters_store = {}
    filters_store[view_key] = deepcopy(filters)
    ui_state[SESSION_FILTERS_KEY] = filters_store
    set_ui_state(ui_state)

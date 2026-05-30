"""Tests for customization settings (FEAT-003)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest


def _is_expected_headless_qt_failure(exc: Exception) -> bool:
    if isinstance(exc, ModuleNotFoundError):
        missing_name = getattr(exc, "name", "")
        return missing_name == "PySide6" or missing_name.startswith("PySide6.")
    message = str(exc).lower()
    markers = (
        "libgl.so.1",
        "libegl.so.1",
        "libxkbcommon.so.0",
        "could not load the qt platform plugin",
        "no qt platform plugin could be initialized",
        "qt.qpa.plugin",
        "xcb",
        "offscreen",
    )
    return isinstance(exc, (ImportError, OSError, RuntimeError)) and any(
        marker in message for marker in markers
    )


def _ensure_app() -> object:
    try:
        from PySide6.QtWidgets import QApplication
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_get_appearance_settings_defaults(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    from pathlib import Path

    profile = Path(str(tmp_path)) / "profile"
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(profile))
    import importlib

    import app.runtime_paths
    import app.settings

    importlib.reload(app.runtime_paths)
    importlib.reload(app.settings)
    from app.settings import get_appearance_settings

    settings = get_appearance_settings()
    assert settings["theme"] == "light"
    assert settings["accent_color"] == "#1976D2"
    assert settings["font_size"] == "medium"
    assert settings["custom_logo_path"] is None
    assert settings["custom_icon_path"] is None


def test_update_appearance_settings_roundtrip(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    from pathlib import Path

    profile = Path(str(tmp_path)) / "profile"
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(profile))
    import importlib

    import app.runtime_paths
    import app.settings

    importlib.reload(app.runtime_paths)
    importlib.reload(app.settings)
    from app.settings import get_appearance_settings, update_appearance_settings

    update_appearance_settings({
        "theme": "dark",
        "accent_color": "#388E3C",
        "font_size": "large",
        "custom_logo_path": None,
        "custom_icon_path": None,
    })
    result = get_appearance_settings()
    assert result["theme"] == "dark"
    assert result["accent_color"] == "#388E3C"
    assert result["font_size"] == "large"
    assert result["custom_logo_path"] is None
    assert result["custom_icon_path"] is None


def test_settings_view_has_appearance_section(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    from pathlib import Path

    profile = Path(str(tmp_path)) / "profile"
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(profile))
    import importlib

    import app.runtime_paths
    import app.settings

    importlib.reload(app.runtime_paths)
    importlib.reload(app.settings)

    _ensure_app()

    try:
        from PySide6.QtWidgets import QComboBox, QGroupBox, QPushButton

        from app.ui.settings_view import SettingsView

        view = SettingsView()
        # Find appearance group box
        groups = view.findChildren(QGroupBox)
        appearance_groups = [g for g in groups if g.title() == "Внешний вид"]
        assert len(appearance_groups) == 1, "Should have exactly one 'Внешний вид' group"

        # Check combo boxes exist
        combos = view.findChildren(QComboBox)
        assert len(combos) >= 3, "Should have at least 3 combo boxes (theme, accent, font)"

        # Check apply button exists
        buttons = view.findChildren(QPushButton)
        button_texts = [b.text() for b in buttons]
        assert "Применить" in button_texts
        assert "Логотип..." in button_texts
        assert "Иконка..." in button_texts

        # Existing buttons still present
        assert "Пересчитать рейтинг" in button_texts
        assert "Слияние дублей" in button_texts
        assert "Сезонные переходы" in button_texts
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise


def test_theme_manager_accepts_accent_and_font(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    from pathlib import Path

    profile = Path(str(tmp_path)) / "profile"
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(profile))

    app = _ensure_app()

    try:
        from app.ui.theme import ThemeManager

        # Should not raise
        ThemeManager.apply_theme(app, "light", accent_color="#388E3C", font_size="small")  # type: ignore[arg-type]
        ThemeManager.apply_theme(app, "dark", accent_color="#F57C00", font_size="large")  # type: ignore[arg-type]
        ThemeManager.apply_theme(app, "light", accent_color="", font_size="medium")  # type: ignore[arg-type]
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

from __future__ import annotations

import os

import pytest

from app.db.database import get_connection
from app.db.repositories import PlayerRepository


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytestmark = pytest.mark.release_smoke


def _is_expected_headless_qt_failure(exc: Exception) -> bool:
    if isinstance(exc, ModuleNotFoundError):
        return True
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
    return isinstance(exc, (ImportError, OSError, RuntimeError)) and any(marker in message for marker in markers)


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


def test_diagnostics_view_opens_selected_restore_point_details(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    try:
        _ensure_app()
        from app.services.restore_points import create_restore_point
        from app.ui.diagnostics_view import DiagnosticsView
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    connection = get_connection(tmp_path / "restore-point-details.db")
    PlayerRepository(connection).create(
        {
            "last_name": "Backup",
            "first_name": "Case",
            "middle_name": None,
            "birth_date": None,
            "gender": None,
            "coach": None,
            "club": None,
            "notes": None,
        }
    )
    create_restore_point(
        connection=connection,
        title="Перед импортом",
        reason="tests",
        source="test",
        operation_group_id="op-restore-details",
    )

    opened: list[object] = []

    class FakeRestorePointDetailsDialog:
        def __init__(self, *, record, parent=None) -> None:
            opened.append(record)

        def exec(self) -> int:
            opened.append("exec")
            return 0

    monkeypatch.setattr("app.ui.diagnostics_view.get_connection", lambda: connection)
    monkeypatch.setattr(
        "app.ui.diagnostics_view.RestorePointDetailsDialog",
        FakeRestorePointDetailsDialog,
    )

    view = DiagnosticsView()
    view.restore_points_list.setCurrentRow(0)
    view._open_selected_restore_point_details()

    assert opened[1] == "exec"
    record = opened[0]
    assert record.title == "Перед импортом"
    assert record.reason == "tests"
    assert record.operation_group_id == "op-restore-details"

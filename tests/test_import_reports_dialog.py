from __future__ import annotations

import os

import pytest

from app.db.database import get_connection
from app.services.import_xlsx import ImportApplyReport


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


def test_import_reports_dialog_shows_history_and_export_actions(tmp_path) -> None:
    try:
        _ensure_app()
        from app.services.import_report import build_import_session_report, persist_import_session_report
        from app.ui.import_reports_dialog import ImportReportsDialog
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    connection = get_connection(tmp_path / "import-reports-dialog.db")
    connection.execute(
        """
        INSERT INTO tournaments (name, date, category_code, league_code, source_files, status, has_draft_changes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        ("Dialog Cup", "2026-04-07", "U14", None, "[]", "draft", 1),
    )
    tournament_id = int(connection.execute("SELECT id FROM tournaments ORDER BY id DESC LIMIT 1").fetchone()[0])

    report = build_import_session_report(
        connection=connection,
        apply_report=ImportApplyReport(
            tournament_id=tournament_id,
            tournament_name="Dialog Cup",
            tournament_status="draft",
            has_draft_changes=True,
            imported_rows=2,
            skipped_rows=1,
            total_rows=3,
            warnings=["Needs review"],
            norms_loaded=True,
            source_files=["/tmp/dialog.xlsx"],
            operation_group_id="op-dialog",
            files_processed=1,
            tables_processed=1,
            rows_read=3,
            players_created=1,
            players_reused=1,
            players_matched_manually=1,
        ),
        apply_status="draft_applied",
    )
    persist_import_session_report(connection=connection, report=report)

    dialog = ImportReportsDialog(connection=connection)
    assert dialog.report_list.count() == 1
    dialog.report_list.setCurrentRow(0)
    dialog._sync_selected_report()
    assert dialog.export_txt_button.isEnabled() is True
    assert dialog.export_json_button.isEnabled() is True
    assert "Dialog Cup" in dialog.details_text.toPlainText()


def test_reports_view_opens_import_reports_dialog(monkeypatch) -> None:
    try:
        _ensure_app()
        from app.ui.reports_view import ReportsView
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    opened: list[bool] = []

    class FakeImportReportsDialog:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def exec(self) -> int:
            opened.append(True)
            return 0

    monkeypatch.setattr("app.ui.reports_view.ImportReportsDialog", FakeImportReportsDialog)
    view = ReportsView()
    view._open_import_history()

    assert opened == [True]

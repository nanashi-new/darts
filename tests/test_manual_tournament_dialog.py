from __future__ import annotations

import os
from types import SimpleNamespace

import pytest


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


def test_manual_tournament_dialog_parses_rows() -> None:
    try:
        _ensure_app()
        from app.ui.manual_tournament_dialog import ManualTournamentDialog
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    dialog = ManualTournamentDialog()
    dialog.name_input.setText("Adult Manual Cup")
    dialog.league_code_input.setText("PREMIER")
    dialog.rows_input.setPlainText(
        "Adultov Alex; 1989-01-01; 1; 120; M\n"
        "Senior Sara; 1990; 2; 105; W"
    )

    data = dialog.form_data()

    assert data.tournament_name == "Adult Manual Cup"
    assert data.league_code == "PREMIER"
    assert len(data.rows) == 2
    assert data.rows[0]["points_total"] == "120"
    assert data.rows[0]["gender"] == "M"
    assert data.rows[1]["gender"] == "W"


def test_tournaments_view_uses_manual_adult_dialog(monkeypatch, tmp_path) -> None:
    try:
        _ensure_app()
        from app.ui.tournaments_view import TournamentsView
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    from app.db.database import get_connection

    connection = get_connection(tmp_path / "manual-tournaments-view.db")
    captured: list[tuple[str, str, str | None, list[dict[str, object]]]] = []

    class FakeDialog:
        def __init__(self, parent=None) -> None:
            self.parent = parent

        def exec(self) -> int:
            from PySide6.QtWidgets import QDialog

            return QDialog.DialogCode.Accepted

        def form_data(self):
            return SimpleNamespace(
                tournament_name="Adult UI Cup",
                tournament_date="2026-04-22",
                league_code="PREMIER",
                rows=[{"fio": "Adultov Alex", "birth": "1989", "place": "1", "points_total": "120", "gender": "M"}],
            )

    def fake_create_manual_adult_tournament(*, connection, tournament_name, tournament_date, league_code, rows):
        captured.append((tournament_name, tournament_date, league_code, rows))
        return SimpleNamespace(
            tournament_id=1,
            tournament_name=tournament_name,
            imported_rows=1,
            skipped_rows=0,
            warnings=[],
        )

    monkeypatch.setattr("app.ui.tournaments_view.get_connection", lambda: connection)
    monkeypatch.setattr("app.ui.tournaments_view.ManualTournamentDialog", FakeDialog)
    monkeypatch.setattr(
        "app.ui.tournaments_view.create_manual_adult_tournament",
        fake_create_manual_adult_tournament,
    )
    monkeypatch.setattr("app.ui.tournaments_view.QMessageBox.information", lambda *args, **kwargs: None)

    view = TournamentsView()
    assert hasattr(view, "_create_adult_btn")
    view._create_manual_adult_tournament()

    assert captured == [
        (
            "Adult UI Cup",
            "2026-04-22",
            "PREMIER",
            [{"fio": "Adultov Alex", "birth": "1989", "place": "1", "points_total": "120", "gender": "M"}],
        )
    ]


def test_tournaments_view_archive_uses_safe_wrapper_with_reason(monkeypatch, tmp_path) -> None:
    try:
        _ensure_app()
        from app.db.repositories import TournamentRepository
        from app.ui.tournaments_view import TournamentsView
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    from app.db.database import get_connection

    connection = get_connection(tmp_path / "safe-status-ui.db")
    tournament_id = TournamentRepository(connection).create(
        {
            "name": "Safe UI Cup",
            "date": "2026-04-26",
            "category_code": "U12",
            "status": "confirmed",
            "source_files": "[]",
        }
    )
    captured: list[dict[str, object]] = []

    def fake_archive_or_cancel_tournament(**kwargs):
        captured.append(kwargs)
        return {
            "ok": True,
            "data": {
                "tournament_id": tournament_id,
                "from_status": "confirmed",
                "to_status": "archived",
                "restore_point_created": True,
            },
        }

    monkeypatch.setattr("app.ui.tournaments_view.get_connection", lambda: connection)
    monkeypatch.setattr("app.ui.tournaments_view.archive_or_cancel_tournament", fake_archive_or_cancel_tournament)
    monkeypatch.setattr("app.ui.tournaments_view.QInputDialog.getText", lambda *args, **kwargs: ("Сезон закрыт", True))
    monkeypatch.setattr("app.ui.tournaments_view.QMessageBox.information", lambda *args, **kwargs: None)

    view = TournamentsView()
    view.refresh_latest_tournament(tournament_id)

    assert hasattr(view, "_archive_btn")
    assert hasattr(view, "_cancel_btn")
    assert view._archive_btn.text() == "Архив"
    assert view._cancel_btn.text() == "Отменить"

    view._safe_archive_or_cancel_tournament("archived", "Архивация")

    assert captured
    assert captured[0]["tournament_id"] == tournament_id
    assert captured[0]["target_status"] == "archived"
    assert captured[0]["reason"] == "Сезон закрыт"
    assert captured[0]["actor"] == "tournaments_view"

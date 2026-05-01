from __future__ import annotations

import os

import pytest

from app.db.database import get_connection
from app.db.repositories import PlayerRepository, ResultRepository, TournamentRepository


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytestmark = pytest.mark.release_smoke


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


def test_tournaments_view_opens_selected_result_details(monkeypatch, tmp_path) -> None:
    try:
        _ensure_app()
        from app.ui.tournaments_view import TournamentsView
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    connection = get_connection(tmp_path / "tournament-result-details.db")
    players = PlayerRepository(connection)
    tournaments = TournamentRepository(connection)
    results = ResultRepository(connection)

    player_id = players.create(
        {
            "last_name": "Иванов",
            "first_name": "Иван",
            "middle_name": "Иванович",
            "birth_date": "2012-04-03",
            "gender": "M",
            "coach": "Петров",
            "club": "Лига",
            "notes": None,
        }
    )
    tournament_id = tournaments.create(
        {
            "name": "Кубок деталей",
            "date": "2026-04-26",
            "category_code": "U14",
            "league_code": "PREMIER",
        }
    )
    results.create(
        {
            "tournament_id": tournament_id,
            "player_id": player_id,
            "place": 1,
            "score_set": 320,
            "score_sector20": 45,
            "score_big_round": 14,
            "rank_set": None,
            "rank_sector20": None,
            "rank_big_round": None,
            "points_classification": 0,
            "points_place": 100,
            "points_total": 100,
            "calc_version": "tests",
        }
    )

    opened: list[dict[str, object] | str] = []

    class FakeTournamentResultDetailsDialog:
        def __init__(self, *, result: dict[str, object], parent=None) -> None:
            opened.append(result)

        def exec(self) -> int:
            opened.append("exec")
            return 0

    monkeypatch.setattr("app.ui.tournaments_view.get_connection", lambda: connection)
    monkeypatch.setattr(
        "app.ui.tournaments_view.TournamentResultDetailsDialog",
        FakeTournamentResultDetailsDialog,
    )

    view = TournamentsView()
    view.results_table.selectRow(0)
    view._open_selected_result_details()

    assert opened[1] == "exec"
    result_payload = opened[0]
    assert isinstance(result_payload, dict)
    assert result_payload["fio"] == "Иванов Иван Иванович"
    assert result_payload["birth_date"] == "2012-04-03"
    assert result_payload["points_total"] == 100


def test_tournaments_view_opens_current_tournament_details(monkeypatch, tmp_path) -> None:
    try:
        _ensure_app()
        from app.ui.tournaments_view import TournamentsView
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    connection = get_connection(tmp_path / "tournament-details-view.db")
    tournament_id = TournamentRepository(connection).create(
        {
            "name": "Кубок турнира",
            "date": "2026-04-30",
            "category_code": "U12",
            "league_code": "PREMIER",
            "status": "published",
            "type": "standard",
            "season": "2026",
            "source_files": '["protocol.xlsx"]',
            "warning_state": "none",
            "error_state": "none",
        }
    )
    opened: list[dict[str, object] | str] = []

    class FakeTournamentDetailsDialog:
        def __init__(self, *, tournament: dict[str, object], parent=None) -> None:
            opened.append(tournament)

        def exec(self) -> int:
            opened.append("exec")
            return 0

    monkeypatch.setattr("app.ui.tournaments_view.get_connection", lambda: connection)
    monkeypatch.setattr("app.ui.tournaments_view.TournamentDetailsDialog", FakeTournamentDetailsDialog, raising=False)

    view = TournamentsView()
    view.refresh_latest_tournament(tournament_id)

    assert hasattr(view, "_tournament_details_btn")
    assert view._tournament_details_btn.text() == "Турнир"
    assert "детали выбранного турнира" in view._tournament_details_btn.toolTip().lower()

    view._open_tournament_details()

    assert opened[1] == "exec"
    tournament_payload = opened[0]
    assert isinstance(tournament_payload, dict)
    assert tournament_payload["name"] == "Кубок турнира"
    assert tournament_payload["status"] == "published"


def test_tournament_details_dialog_uses_russian_labels() -> None:
    try:
        _ensure_app()
        from app.ui.tournament_details_dialog import TournamentDetailsDialog
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    dialog = TournamentDetailsDialog(
        tournament={
            "id": 42,
            "name": "Кубок деталей",
            "date": "2026-04-30",
            "category_code": "U12",
            "league_code": "PREMIER",
            "status": "published",
            "type": "standard",
            "season": "2026",
            "series": "Весна",
            "location": "Москва",
            "organizer": "Школа дартса",
            "source_files": '["protocol.xlsx", "adult.xlsx"]',
            "has_draft_changes": 0,
            "warning_state": "none",
            "error_state": "none",
            "confirmed_by": "admin",
            "published_by": "admin",
        }
    )

    from PySide6.QtWidgets import QLabel

    visible_text = "\n".join(label.text() for label in dialog.findChildren(QLabel))

    assert "Статус" in visible_text
    assert "Опубликован" in visible_text
    assert "Категория" in visible_text
    assert "До 12 лет" in visible_text
    assert "Лига" in visible_text
    assert "Премьер-лига" in visible_text
    assert "Тип" in visible_text
    assert "обычный" in visible_text
    assert "Файлы источника" in visible_text
    assert "protocol.xlsx" in visible_text
    assert "published" not in visible_text
    assert "standard" not in visible_text

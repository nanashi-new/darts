from __future__ import annotations

import os

import pytest

from app.db.database import get_connection
from app.db.repositories import PlayerRepository, ResultRepository, TournamentRepository
from app.services.tournament_lifecycle import transition_tournament_status


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


def test_players_view_shows_league_history_for_selected_player(monkeypatch, tmp_path) -> None:
    try:
        _ensure_app()
        from app.ui.players_view import PlayersView
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    connection = get_connection(tmp_path / "players-view-league-history.db")
    players = PlayerRepository(connection)
    tournaments = TournamentRepository(connection)
    results = ResultRepository(connection)
    player_id = players.create(
        {
            "last_name": "League",
            "first_name": "Player",
            "middle_name": None,
            "birth_date": None,
            "gender": None,
            "coach": None,
            "club": None,
            "notes": None,
        }
    )
    tournament_id = tournaments.create(
        {
            "name": "League History Cup",
            "date": "2026-04-25",
            "category_code": "U18",
            "league_code": "PREMIER",
            "is_adult_mode": 0,
            "source_files": "[]",
            "status": "draft",
            "has_draft_changes": 1,
        }
    )
    results.create(
        {
            "tournament_id": tournament_id,
            "player_id": player_id,
            "place": 1,
            "score_set": 0,
            "score_sector20": 0,
            "score_big_round": 0,
            "rank_set": None,
            "rank_sector20": None,
            "rank_big_round": None,
            "points_classification": 0,
            "points_place": 120,
            "points_total": 120,
            "calc_version": "tests",
        }
    )
    for target in ("review", "confirmed", "published"):
        assert transition_tournament_status(
            connection=connection,
            tournament_id=tournament_id,
            to_status=target,
            context={"actor": "tests", "operation_group_id": "op-player-view-league"},
        )["ok"] is True

    monkeypatch.setattr("app.ui.players_view.get_connection", lambda: connection)
    view = PlayersView()
    view._players_table.selectRow(0)
    view._on_player_selected()

    assert hasattr(view, "_league_history_table")
    assert view._league_history_table.model() is not None
    assert view._league_history_table.model().rowCount() == 1


def test_players_view_opens_player_card_for_selected_player(monkeypatch, tmp_path) -> None:
    try:
        _ensure_app()
        from app.ui.players_view import PlayersView
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    connection = get_connection(tmp_path / "players-view-open-card.db")
    players = PlayerRepository(connection)
    player_id = players.create(
        {
            "last_name": "Card",
            "first_name": "Casey",
            "middle_name": None,
            "birth_date": None,
            "gender": None,
            "coach": None,
            "club": None,
            "notes": None,
        }
    )

    opened: list[int] = []

    class FakePlayerCardDialog:
        def __init__(self, *, connection, player_id, parent=None) -> None:
            opened.append(player_id)

        def exec(self) -> int:
            return 0

    monkeypatch.setattr("app.ui.players_view.get_connection", lambda: connection)
    monkeypatch.setattr("app.ui.players_view.PlayerCardDialog", FakePlayerCardDialog)

    view = PlayersView()
    view._players_table.selectRow(0)
    view._open_player_card()

    assert opened == [player_id]

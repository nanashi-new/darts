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


def _create_player_context_fixture(connection) -> int:
    players = PlayerRepository(connection)
    tournaments = TournamentRepository(connection)
    results = ResultRepository(connection)
    player_id = players.create(
        {
            "last_name": "Context",
            "first_name": "Casey",
            "middle_name": None,
            "birth_date": "2011-05-09",
            "gender": "F",
            "coach": "Coach Zero",
            "club": "Vector Club",
            "notes": "Promising player",
        }
    )
    tournament_id = tournaments.create(
        {
            "name": "Player Card Cup",
            "date": "2026-04-26",
            "category_code": "U16",
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
            "points_place": 130,
            "points_total": 130,
            "calc_version": "tests",
        }
    )
    for target in ("review", "confirmed", "published"):
        assert transition_tournament_status(
            connection=connection,
            tournament_id=tournament_id,
            to_status=target,
            context={"actor": "tests", "operation_group_id": "op-player-card"},
        )["ok"] is True
    return player_id


def test_player_card_dialog_shows_overview_and_context_tables(tmp_path) -> None:
    try:
        _ensure_app()
        from app.ui.player_card_dialog import PlayerCardDialog
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    connection = get_connection(tmp_path / "player-card-dialog.db")
    player_id = _create_player_context_fixture(connection)
    from app.services.notes import create_note
    from app.services.training_journal import create_training_entry

    create_note(
        connection=connection,
        entity_type="player",
        entity_id=str(player_id),
        note_type="player_note",
        visibility="internal_service",
        title="Card note",
        body="Player card should show this note.",
        priority="normal",
        author="tests",
    )
    create_training_entry(
        connection=connection,
        player_id=player_id,
        coach_name="Coach Zero",
        training_date="2026-04-27",
        session_type="follow_up",
        summary="Training journal row",
        goals="Keep form stable",
        metrics={"sets": 3},
        related_tournament_id=None,
        next_action="Review after weekend",
    )

    dialog = PlayerCardDialog(connection=connection, player_id=player_id)

    assert "Context Casey" in dialog.windowTitle()
    assert "Coach Zero" in dialog.overview_label.text()
    assert dialog.tournament_history_table.rowCount() == 1
    assert dialog.league_history_table.rowCount() == 1
    assert dialog.rating_state_table.rowCount() >= 1
    assert dialog.notes_table.rowCount() == 1
    assert dialog.training_table.rowCount() == 1
    assert hasattr(dialog, "coach_note_button")
    assert hasattr(dialog, "all_notes_button")
    assert hasattr(dialog, "add_training_button")

"""Tests for Player Card v2 tabbed interface."""

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


def _create_empty_player(connection) -> int:
    """Create a player with no tournaments/notes/training."""
    players = PlayerRepository(connection)
    player_id = players.create(
        {
            "last_name": "Empty",
            "first_name": "Player",
            "middle_name": None,
            "birth_date": "2010-01-01",
            "gender": "M",
            "coach": "Coach A",
            "club": "Test Club",
            "notes": "",
        }
    )
    return player_id


def _create_player_with_history(connection) -> int:
    """Create a player with tournament results, notes, and training."""
    players = PlayerRepository(connection)
    tournaments = TournamentRepository(connection)
    results = ResultRepository(connection)

    player_id = players.create(
        {
            "last_name": "Active",
            "first_name": "Player",
            "middle_name": None,
            "birth_date": "2009-03-15",
            "gender": "F",
            "coach": "Coach B",
            "club": "Star Club",
            "notes": "Active player",
        }
    )

    # Create two tournaments
    for i, (name, date, place, points) in enumerate(
        [
            ("Cup Alpha", "2026-01-10", 2, 100),
            ("Cup Beta", "2026-02-20", 1, 150),
        ]
    ):
        tid = tournaments.create(
            {
                "name": name,
                "date": date,
                "category_code": "U15",
                "league_code": "PREMIER",
                "is_adult_mode": 0,
                "source_files": "[]",
                "status": "draft",
                "has_draft_changes": 1,
            }
        )
        results.create(
            {
                "tournament_id": tid,
                "player_id": player_id,
                "place": place,
                "score_set": 0,
                "score_sector20": 0,
                "score_big_round": 0,
                "rank_set": None,
                "rank_sector20": None,
                "rank_big_round": None,
                "points_classification": 0,
                "points_place": points,
                "points_total": points,
                "calc_version": "tests",
            }
        )
        for target in ("review", "confirmed", "published"):
            assert transition_tournament_status(
                connection=connection,
                tournament_id=tid,
                to_status=target,
                context={"actor": "tests", "operation_group_id": f"op-v2-{i}"},
            )["ok"] is True

    # Add notes
    from app.services.notes import create_note

    create_note(
        connection=connection,
        entity_type="player",
        entity_id=str(player_id),
        note_type="player_note",
        visibility="internal_service",
        title="Player note 1",
        body="Body 1",
        priority="normal",
        author="tests",
    )
    create_note(
        connection=connection,
        entity_type="player",
        entity_id=str(player_id),
        note_type="coach_note",
        visibility="coach_only",
        title="Coach note 1",
        body="Body 2",
        priority="high",
        author="coach",
    )

    # Add training
    from app.services.training_journal import create_training_entry

    create_training_entry(
        connection=connection,
        player_id=player_id,
        coach_name="Coach B",
        training_date="2026-03-01",
        session_type="general",
        summary="Good session",
        goals="Improve accuracy",
        metrics={"sets": 5},
        related_tournament_id=None,
        next_action="Practice more",
    )

    return player_id


def test_dialog_has_tab_widget_with_6_tabs(tmp_path) -> None:
    try:
        _ensure_app()
        from PySide6.QtWidgets import QTabWidget

        from app.ui.player_card_dialog import PlayerCardDialog
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    connection = get_connection(tmp_path / "v2-tabs.db")
    player_id = _create_empty_player(connection)
    dialog = PlayerCardDialog(connection=connection, player_id=player_id)

    tab_widget = dialog.findChild(QTabWidget)
    assert tab_widget is not None
    assert tab_widget.count() == 6

    expected_tabs = ["Общее", "Рейтинг", "Турниры", "Заметки", "Тренировки", "История"]
    actual_tabs = [tab_widget.tabText(i) for i in range(tab_widget.count())]
    assert actual_tabs == expected_tabs


def test_empty_player_shows_zero_summaries(tmp_path) -> None:
    try:
        _ensure_app()
        from app.ui.player_card_dialog import PlayerCardDialog
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    connection = get_connection(tmp_path / "v2-empty.db")
    player_id = _create_empty_player(connection)
    dialog = PlayerCardDialog(connection=connection, player_id=player_id)

    assert "Всего турниров: 0" in dialog.tournament_summary_label.text()
    assert "Всего тренировок: 0" in dialog.training_summary_label.text()


def test_player_with_history_shows_correct_tournament_count(tmp_path) -> None:
    try:
        _ensure_app()
        from app.ui.player_card_dialog import PlayerCardDialog
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    connection = get_connection(tmp_path / "v2-history.db")
    player_id = _create_player_with_history(connection)
    dialog = PlayerCardDialog(connection=connection, player_id=player_id)

    assert "Всего турниров: 2" in dialog.tournament_summary_label.text()
    assert "Лучшее место: 1" in dialog.tournament_summary_label.text()
    assert dialog.tournament_history_table.rowCount() == 2


def test_notes_filter_combo_exists_with_4_items(tmp_path) -> None:
    try:
        _ensure_app()
        from app.ui.player_card_dialog import PlayerCardDialog
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    connection = get_connection(tmp_path / "v2-filter.db")
    player_id = _create_empty_player(connection)
    dialog = PlayerCardDialog(connection=connection, player_id=player_id)

    assert hasattr(dialog, "notes_filter_combo")
    assert dialog.notes_filter_combo.count() == 4


def test_notes_filter_filters_notes(tmp_path) -> None:
    try:
        _ensure_app()
        from app.ui.player_card_dialog import PlayerCardDialog
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    connection = get_connection(tmp_path / "v2-filter2.db")
    player_id = _create_player_with_history(connection)
    dialog = PlayerCardDialog(connection=connection, player_id=player_id)

    # All notes
    assert dialog.notes_table.rowCount() == 2

    # Filter to player_note only
    dialog.notes_filter_combo.setCurrentIndex(1)  # "Заметка игрока"
    assert dialog.notes_table.rowCount() == 1

    # Filter to coach_note only
    dialog.notes_filter_combo.setCurrentIndex(2)  # "Заметка тренера"
    assert dialog.notes_table.rowCount() == 1

    # Filter to follow_up (none exist)
    dialog.notes_filter_combo.setCurrentIndex(3)  # "Контрольное действие"
    assert dialog.notes_table.rowCount() == 0

    # Back to all
    dialog.notes_filter_combo.setCurrentIndex(0)  # "Все"
    assert dialog.notes_table.rowCount() == 2


def test_rating_trend_label_exists(tmp_path) -> None:
    try:
        _ensure_app()
        from app.ui.player_card_dialog import PlayerCardDialog
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    connection = get_connection(tmp_path / "v2-trend.db")
    player_id = _create_empty_player(connection)
    dialog = PlayerCardDialog(connection=connection, player_id=player_id)

    assert hasattr(dialog, "rating_trend_label")
    assert "Динамика:" in dialog.rating_trend_label.text()


def test_placeholder_groupboxes_exist(tmp_path) -> None:
    try:
        _ensure_app()
        from PySide6.QtWidgets import QGroupBox

        from app.ui.player_card_dialog import PlayerCardDialog
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    connection = get_connection(tmp_path / "v2-placeholder.db")
    player_id = _create_empty_player(connection)
    dialog = PlayerCardDialog(connection=connection, player_id=player_id)

    # Find all group boxes
    group_boxes = dialog.findChildren(QGroupBox)
    titles = [gb.title() for gb in group_boxes]

    assert "Теги" in titles
    assert "Кастомные поля" in titles
    assert "Вложения" in titles

    # Verify real widgets replaced placeholders
    from app.ui.tags_widget import TagsWidget
    from app.ui.attachments_widget import AttachmentsWidget
    from app.ui.custom_fields_widget import CustomFieldsWidget

    assert hasattr(dialog, "tags_widget")
    assert isinstance(dialog.tags_widget, TagsWidget)
    assert hasattr(dialog, "custom_fields_widget")
    assert isinstance(dialog.custom_fields_widget, CustomFieldsWidget)
    assert hasattr(dialog, "attachments_widget")
    assert isinstance(dialog.attachments_widget, AttachmentsWidget)


def test_training_summary_shows_last_date(tmp_path) -> None:
    try:
        _ensure_app()
        from app.ui.player_card_dialog import PlayerCardDialog
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    connection = get_connection(tmp_path / "v2-training.db")
    player_id = _create_player_with_history(connection)
    dialog = PlayerCardDialog(connection=connection, player_id=player_id)

    assert "Всего тренировок: 1" in dialog.training_summary_label.text()
    assert "2026-03-01" in dialog.training_summary_label.text()

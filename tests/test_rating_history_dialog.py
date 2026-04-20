from __future__ import annotations

import os

import pytest

from app.db.database import get_connection
from app.db.repositories import PlayerRepository, ResultRepository, TournamentRepository


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


def _create_snapshot_fixture(connection) -> None:
    tournaments = TournamentRepository(connection)
    players = PlayerRepository(connection)
    results = ResultRepository(connection)
    player_one = players.create(
        {
            "last_name": "Adams",
            "first_name": "Alice",
            "middle_name": None,
            "birth_date": None,
            "gender": None,
            "coach": None,
            "club": None,
            "notes": None,
        }
    )
    player_two = players.create(
        {
            "last_name": "Brown",
            "first_name": "Bob",
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
            "name": "History Cup",
            "date": "2026-04-09",
            "category_code": "U14",
            "league_code": "PREMIER",
            "source_files": "[]",
            "status": "published",
            "has_draft_changes": 0,
        }
    )
    results.create(
        {
            "tournament_id": tournament_id,
            "player_id": player_one,
            "place": 1,
            "score_set": 0,
            "score_sector20": 0,
            "score_big_round": 0,
            "rank_set": None,
            "rank_sector20": None,
            "rank_big_round": None,
            "points_classification": 0,
            "points_place": 100,
            "points_total": 100,
            "calc_version": "tests",
        }
    )
    results.create(
        {
            "tournament_id": tournament_id,
            "player_id": player_two,
            "place": 2,
            "score_set": 0,
            "score_sector20": 0,
            "score_big_round": 0,
            "rank_set": None,
            "rank_sector20": None,
            "rank_big_round": None,
            "points_classification": 0,
            "points_place": 90,
            "points_total": 90,
            "calc_version": "tests",
        }
    )

    from app.services.rating_snapshot import create_rating_snapshot_for_tournament_publish

    result = create_rating_snapshot_for_tournament_publish(
        connection=connection,
        tournament_id=tournament_id,
        n_value=6,
        operation_group_id="op-history-dialog",
    )
    assert result.created is True


def _create_adult_snapshot_fixture(connection) -> None:
    tournaments = TournamentRepository(connection)
    players = PlayerRepository(connection)
    results = ResultRepository(connection)
    player_one = players.create(
        {
            "last_name": "Adultov",
            "first_name": "Alex",
            "middle_name": None,
            "birth_date": None,
            "gender": "male",
            "coach": None,
            "club": None,
            "notes": None,
        }
    )
    player_two = players.create(
        {
            "last_name": "Senior",
            "first_name": "Sara",
            "middle_name": None,
            "birth_date": None,
            "gender": "female",
            "coach": None,
            "club": None,
            "notes": None,
        }
    )
    player_three = players.create(
        {
            "last_name": "Unknown",
            "first_name": "Pat",
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
            "name": "Adult History Cup",
            "date": "2026-04-10",
            "category_code": None,
            "league_code": None,
            "is_adult_mode": 1,
            "source_files": "[]",
            "status": "published",
            "has_draft_changes": 0,
        }
    )
    for place, player_id, points in ((1, player_one, 120), (2, player_two, 105), (3, player_three, 90)):
        results.create(
            {
                "tournament_id": tournament_id,
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

    from app.services.rating_snapshot import create_rating_snapshot_for_tournament_publish

    result = create_rating_snapshot_for_tournament_publish(
        connection=connection,
        tournament_id=tournament_id,
        n_value=6,
        operation_group_id="op-adult-history-dialog",
    )
    assert result.created is True


def test_rating_history_dialog_shows_sessions_rows_and_basis(tmp_path) -> None:
    try:
        _ensure_app()
        from app.ui.rating_history_dialog import RatingHistoryDialog
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    connection = get_connection(tmp_path / "rating-history-dialog.db")
    _create_snapshot_fixture(connection)

    dialog = RatingHistoryDialog(connection=connection, scope_type="category", scope_key="U14")
    assert dialog.session_list.count() == 1
    dialog.session_list.setCurrentRow(0)
    dialog._sync_selected_session()
    assert dialog.rows_table.rowCount() == 2
    dialog.rows_table.selectRow(0)
    dialog._sync_selected_row()
    assert dialog.basis_list.count() >= 1
    assert "Adams Alice" in dialog.status_label.text()


def test_rating_view_opens_history_dialog_for_selected_category(monkeypatch, tmp_path) -> None:
    try:
        _ensure_app()
        from app.ui.rating_view import RatingView
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    connection = get_connection(tmp_path / "rating-view-history.db")
    _create_snapshot_fixture(connection)

    opened: list[tuple[str, str]] = []

    class FakeRatingHistoryDialog:
        def __init__(self, *, connection, scope_type, scope_key, parent=None) -> None:
            opened.append((scope_type, scope_key))

        def exec(self) -> int:
            return 0

    monkeypatch.setattr("app.ui.rating_view.get_connection", lambda: connection)
    monkeypatch.setattr("app.ui.rating_view.RatingHistoryDialog", FakeRatingHistoryDialog)

    view = RatingView()
    assert view._history_button.isEnabled() is False
    view._category_combo.setCurrentIndex(1)
    view._refresh_history_button_state()
    assert view._history_button.isEnabled() is True

    view._open_rating_history()
    assert opened == [("category", "U14")]


def test_rating_view_opens_history_dialog_for_selected_league(monkeypatch, tmp_path) -> None:
    try:
        _ensure_app()
        from app.ui.rating_view import RatingView
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    connection = get_connection(tmp_path / "rating-view-league-history.db")
    _create_snapshot_fixture(connection)

    opened: list[tuple[str, str]] = []

    class FakeRatingHistoryDialog:
        def __init__(self, *, connection, scope_type, scope_key, parent=None) -> None:
            opened.append((scope_type, scope_key))

        def exec(self) -> int:
            return 0

    monkeypatch.setattr("app.ui.rating_view.get_connection", lambda: connection)
    monkeypatch.setattr("app.ui.rating_view.RatingHistoryDialog", FakeRatingHistoryDialog)

    view = RatingView()
    view._scope_type_combo.setCurrentIndex(1)
    view._refresh_scope_key_options()
    view._category_combo.setCurrentIndex(1)
    view._refresh_history_button_state()

    assert view._history_button.isEnabled() is True
    view._open_rating_history()
    assert opened == [("league", "PREMIER")]


def test_rating_history_dialog_shows_adult_scope_rows(tmp_path) -> None:
    try:
        _ensure_app()
        from app.ui.rating_history_dialog import RatingHistoryDialog
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    connection = get_connection(tmp_path / "rating-history-adult-dialog.db")
    _create_adult_snapshot_fixture(connection)

    dialog = RatingHistoryDialog(connection=connection, scope_type="adult", scope_key="overall")
    assert dialog.session_list.count() == 1
    dialog.session_list.setCurrentRow(0)
    dialog._sync_selected_session()
    assert dialog.rows_table.rowCount() == 3
    assert "adult:overall" in dialog.status_label.text().lower()


def test_rating_view_opens_history_dialog_for_adult_scope(monkeypatch, tmp_path) -> None:
    try:
        _ensure_app()
        from app.ui.rating_view import RatingView
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    connection = get_connection(tmp_path / "rating-view-adult-history.db")
    _create_adult_snapshot_fixture(connection)

    opened: list[tuple[str, str]] = []

    class FakeRatingHistoryDialog:
        def __init__(self, *, connection, scope_type, scope_key, parent=None) -> None:
            opened.append((scope_type, scope_key))

        def exec(self) -> int:
            return 0

    monkeypatch.setattr("app.ui.rating_view.get_connection", lambda: connection)
    monkeypatch.setattr("app.ui.rating_view.RatingHistoryDialog", FakeRatingHistoryDialog)

    view = RatingView()
    adult_index = view._scope_type_combo.findData("adult")
    assert adult_index >= 0
    view._scope_type_combo.setCurrentIndex(adult_index)
    view._refresh_scope_key_options()
    view._category_combo.setCurrentIndex(1)
    view._refresh_history_button_state()

    assert view._history_button.isEnabled() is True
    view._open_rating_history()
    assert opened == [("adult", "overall")]


def test_rating_history_dialog_shows_adult_men_scope_rows(tmp_path) -> None:
    try:
        _ensure_app()
        from app.ui.rating_history_dialog import RatingHistoryDialog
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    connection = get_connection(tmp_path / "rating-history-adult-men-dialog.db")
    _create_adult_snapshot_fixture(connection)

    dialog = RatingHistoryDialog(connection=connection, scope_type="adult", scope_key="men")
    assert dialog.session_list.count() == 1
    dialog.session_list.setCurrentRow(0)
    dialog._sync_selected_session()
    assert dialog.rows_table.rowCount() == 1
    assert "adult:men" in dialog.status_label.text().lower()


def test_rating_view_opens_history_dialog_for_adult_men_scope(monkeypatch, tmp_path) -> None:
    try:
        _ensure_app()
        from app.ui.rating_view import RatingView
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    connection = get_connection(tmp_path / "rating-view-adult-men-history.db")
    _create_adult_snapshot_fixture(connection)

    opened: list[tuple[str, str]] = []

    class FakeRatingHistoryDialog:
        def __init__(self, *, connection, scope_type, scope_key, parent=None) -> None:
            opened.append((scope_type, scope_key))

        def exec(self) -> int:
            return 0

    monkeypatch.setattr("app.ui.rating_view.get_connection", lambda: connection)
    monkeypatch.setattr("app.ui.rating_view.RatingHistoryDialog", FakeRatingHistoryDialog)

    view = RatingView()
    adult_index = view._scope_type_combo.findData("adult")
    assert adult_index >= 0
    view._scope_type_combo.setCurrentIndex(adult_index)
    view._refresh_scope_key_options()
    men_index = view._category_combo.findData("men")
    assert men_index >= 0
    view._category_combo.setCurrentIndex(men_index)
    view._refresh_history_button_state()

    assert view._history_button.isEnabled() is True
    view._open_rating_history()
    assert opened == [("adult", "men")]

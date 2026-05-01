from __future__ import annotations

import os

import pytest

from app.db.database import get_connection
from app.db.repositories import PlayerRepository
from app.services.notes import create_note
from app.services.training_journal import create_training_entry


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


def _create_player(connection) -> int:
    return PlayerRepository(connection).create(
        {
            "last_name": "Иванов",
            "first_name": "Иван",
            "middle_name": "Иванович",
            "birth_date": "2012-04-03",
            "gender": "M",
            "coach": "Петров",
            "club": "Дартс Лига",
            "notes": None,
        }
    )


def test_context_view_opens_selected_note_details(monkeypatch, tmp_path) -> None:
    try:
        _ensure_app()
        from app.ui.context_view import ContextView
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    connection = get_connection(tmp_path / "context-note-details.db")
    player_id = _create_player(connection)
    create_note(
        connection=connection,
        entity_type="player",
        entity_id=str(player_id),
        note_type="coach_note",
        visibility="coach_only",
        title="Длинная заметка",
        body="Подробный план подготовки к следующему турниру.",
        priority="high",
        author="Тренер",
        is_pinned=True,
    )
    opened: list[object] = []

    class FakeNoteDetailsDialog:
        def __init__(self, *, note, parent=None) -> None:
            opened.append(note)

        def exec(self) -> int:
            opened.append("exec")
            return 0

    monkeypatch.setattr("app.ui.context_view.get_connection", lambda: connection)
    monkeypatch.setattr("app.ui.context_view.ContextNoteDetailsDialog", FakeNoteDetailsDialog, raising=False)

    view = ContextView()
    view.notes_table.selectRow(0)

    assert hasattr(view, "open_note_details_button")
    assert view.open_note_details_button.text() == "Детали"
    assert "детали выбранной заметки" in view.open_note_details_button.toolTip().lower()

    view._open_selected_note_details()

    assert opened[1] == "exec"
    note = opened[0]
    assert note.title == "Длинная заметка"
    assert note.body == "Подробный план подготовки к следующему турниру."


def test_context_view_opens_selected_training_details(monkeypatch, tmp_path) -> None:
    try:
        _ensure_app()
        from app.ui.context_view import ContextView
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    connection = get_connection(tmp_path / "context-training-details.db")
    player_id = _create_player(connection)
    create_training_entry(
        connection=connection,
        player_id=player_id,
        coach_name="Петров",
        training_date="2026-05-01",
        session_type="technique",
        summary="Работа над стабильностью броска.",
        goals="Закрепить серию из 10 подходов.",
        metrics={"180": 2, "doubles": "7/20"},
        related_tournament_id=None,
        next_action="Проверить прогресс через неделю.",
    )
    opened: list[object] = []

    class FakeTrainingDetailsDialog:
        def __init__(self, *, entry, parent=None) -> None:
            opened.append(entry)

        def exec(self) -> int:
            opened.append("exec")
            return 0

    monkeypatch.setattr("app.ui.context_view.get_connection", lambda: connection)
    monkeypatch.setattr("app.ui.context_view.ContextTrainingDetailsDialog", FakeTrainingDetailsDialog, raising=False)

    view = ContextView()
    view._tabs.setCurrentIndex(1)
    view.training_table.selectRow(0)

    assert hasattr(view, "open_training_details_button")
    assert view.open_training_details_button.text() == "Детали"
    assert "детали выбранной тренировки" in view.open_training_details_button.toolTip().lower()

    view._open_selected_training_details()

    assert opened[1] == "exec"
    entry = opened[0]
    assert entry.summary == "Работа над стабильностью броска."
    assert entry.next_action == "Проверить прогресс через неделю."


def test_context_detail_dialogs_use_russian_labels() -> None:
    try:
        _ensure_app()
        from PySide6.QtWidgets import QLabel
        from app.services.notes import NoteRecord
        from app.services.training_journal import TrainingEntryRecord
        from app.ui.context_details_dialog import ContextNoteDetailsDialog, ContextTrainingDetailsDialog
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    note_dialog = ContextNoteDetailsDialog(
        note=NoteRecord(
            id=1,
            entity_type="player",
            entity_id="7",
            note_type="coach_note",
            visibility="coach_only",
            author="Тренер",
            title="Контрольная заметка",
            body="Длинный текст заметки.",
            priority="high",
            is_pinned=True,
            is_archived=False,
            created_at="2026-05-01T10:00:00",
            updated_at="2026-05-01T10:30:00",
            entity_label="Иванов Иван",
        )
    )
    training_dialog = ContextTrainingDetailsDialog(
        entry=TrainingEntryRecord(
            id=2,
            player_id=7,
            player_fio="Иванов Иван",
            coach_name="Тренер",
            training_date="2026-05-01",
            session_type="technique",
            summary="Итоги тренировки.",
            goals="Цели тренировки.",
            metrics={"180": 2},
            related_tournament_id=None,
            tournament_name=None,
            next_action="Следующее действие.",
            is_archived=False,
            created_at="2026-05-01T10:00:00",
            updated_at="2026-05-01T10:30:00",
        )
    )

    visible_text = "\n".join(
        label.text()
        for dialog in [note_dialog, training_dialog]
        for label in dialog.findChildren(QLabel)
    )

    assert "Объект" in visible_text
    assert "Заметка тренера" in visible_text
    assert "Только тренеру" in visible_text
    assert "Высокий" in visible_text
    assert "Техника" in visible_text
    assert "Метрики" in visible_text
    assert "Следующее действие." in visible_text
    assert "coach_note" not in visible_text
    assert "coach_only" not in visible_text
    assert "technique" not in visible_text

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


pytestmark = pytest.mark.release_smoke

DISALLOWED_VISIBLE_FRAGMENTS = (
    "Dashboard",
    "Recent tournaments",
    "Recent import reports",
    "Follow-up notes",
    "Diagnostics summary",
    "Self-check",
    "restore point",
    "Restore point",
    "diagnostic bundle",
    "Notes",
    "Training",
    "Search notes",
    "Search training",
    "Open related entity",
    "Open player card",
    "Coach note",
    "Add training",
    "League notes",
    "Adult draft",
    "Adult tournament",
    "Rating Impact Preview",
    "League Transfer Preview",
    "Scope type",
    "Scope key",
    "Title is required",
    "Body is required",
    "Summary is required",
    "Primary",
    "Duplicate",
)


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


def _collect_visible_text(widget) -> list[str]:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QAbstractButton,
        QComboBox,
        QGroupBox,
        QLabel,
        QLineEdit,
        QPlainTextEdit,
        QTabWidget,
        QTableView,
        QTableWidget,
        QTextEdit,
        QWidget,
    )

    chunks: list[str] = []
    widgets = [widget, *widget.findChildren(QWidget)]
    for child in widgets:
        if child.windowTitle():
            chunks.append(child.windowTitle())
        if isinstance(child, QLabel):
            chunks.append(child.text())
        if isinstance(child, QAbstractButton):
            chunks.append(child.text())
        if isinstance(child, QGroupBox):
            chunks.append(child.title())
        if isinstance(child, QLineEdit):
            chunks.append(child.placeholderText())
        if isinstance(child, (QTextEdit, QPlainTextEdit)):
            chunks.append(child.placeholderText())
            chunks.append(child.toPlainText())
        if isinstance(child, QComboBox):
            chunks.extend(child.itemText(index) for index in range(child.count()))
        if isinstance(child, QTabWidget):
            chunks.extend(child.tabText(index) for index in range(child.count()))
        if isinstance(child, QTableWidget):
            for column in range(child.columnCount()):
                item = child.horizontalHeaderItem(column)
                if item is not None:
                    chunks.append(item.text())
        if isinstance(child, QTableView):
            model = child.model()
            if model is not None:
                for column in range(model.columnCount()):
                    value = model.headerData(column, Qt.Orientation.Horizontal)
                    if value:
                        chunks.append(str(value))
    return [chunk for chunk in chunks if chunk]


def test_visible_ui_text_does_not_use_english_working_labels(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    try:
        _ensure_app()
        from app.ui.entity_notes_dialog import EntityNoteDialog, EntityNotesDialog
        from app.ui.main_window import MainWindow
        from app.ui.manual_tournament_dialog import ManualTournamentDialog
        from app.ui.player_edit_dialog import PlayerEditDialog
        from app.ui.training_entry_dialog import TrainingEntryDialog
        from app.db.database import get_connection

        connection = get_connection(tmp_path / "ui-russian-text.db")
        widgets = [
            MainWindow(),
            EntityNoteDialog(),
            EntityNotesDialog(connection=connection, entity_type="league", entity_id="PREMIER"),
            TrainingEntryDialog(),
            ManualTournamentDialog(),
            PlayerEditDialog(),
        ]
    except Exception as exc:  # noqa: BLE001
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    visible_text = "\n".join(text.strip() for widget in widgets for text in _collect_visible_text(widget))
    for fragment in DISALLOWED_VISIBLE_FRAGMENTS:
        assert fragment not in visible_text

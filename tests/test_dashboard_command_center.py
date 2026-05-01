from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


pytestmark = pytest.mark.release_smoke


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


def _visible_text(widget) -> str:
    from PySide6.QtWidgets import QGroupBox, QLabel, QPushButton, QTableWidget, QWidget

    chunks: list[str] = []
    for child in [widget, *widget.findChildren(QWidget)]:
        if isinstance(child, QLabel):
            chunks.append(child.text())
        if isinstance(child, QPushButton):
            chunks.append(child.text())
            chunks.append(child.toolTip())
        if isinstance(child, QGroupBox):
            chunks.append(child.title())
        if isinstance(child, QTableWidget):
            for column in range(child.columnCount()):
                item = child.horizontalHeaderItem(column)
                if item is not None:
                    chunks.append(item.text())
            for row in range(child.rowCount()):
                for column in range(child.columnCount()):
                    item = child.item(row, column)
                    if item is not None:
                        chunks.append(item.text())
    return "\n".join(chunk for chunk in chunks if chunk)


def test_dashboard_command_center_shows_status_counts_and_attention(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    _ensure_app()

    from app.db.database import get_connection
    from app.db.repositories import PlayerRepository, TournamentRepository
    from app.services.import_report import ImportSessionReport, persist_import_session_report
    from app.services.notes import create_note
    from app.settings import set_last_self_check
    from app.ui.dashboard_view import DashboardView

    connection = get_connection()
    player_id = PlayerRepository(connection).create(
        {
            "last_name": "Иванова",
            "first_name": "Анна",
            "middle_name": "",
            "birth_date": "2012-01-01",
            "gender": "female",
            "coach": "",
            "club": "Дартс Лига",
            "notes": "",
        }
    )
    tournament_repo = TournamentRepository(connection)
    tournament_repo.create({"name": "Черновой кубок", "date": "2026-05-01", "status": "draft"})
    review_tournament_id = tournament_repo.create(
        {"name": "Турнир на проверке", "date": "2026-05-02", "status": "review"}
    )
    tournament_repo.create({"name": "Опубликованный турнир", "date": "2026-05-03", "status": "published"})
    create_note(
        connection=connection,
        entity_type="player",
        entity_id=str(player_id),
        note_type="follow_up",
        visibility="coach",
        title="Связаться после турнира",
        body="Проверить прогресс.",
    )
    persist_import_session_report(
        connection=connection,
        report=ImportSessionReport(
            operation_group_id="op-dashboard",
            tournament_id=review_tournament_id,
            tournament_name="Турнир на проверке",
            category_code=None,
            tournament_status="review",
            apply_status="draft_applied",
            files_processed=1,
            tables_processed=1,
            rows_read=3,
            rows_imported=2,
            rows_skipped=1,
            players_created=1,
            players_reused=1,
            players_matched_manually=0,
            warnings=["Не заполнен клуб"],
            warnings_count=1,
            errors_count=0,
            source_files=["import.xlsx"],
        ),
    )
    connection.execute(
        """
        INSERT INTO restore_points (title, reason, file_path, source)
        VALUES (?, ?, ?, ?)
        """,
        ("Перед публикацией", "Проверка главной", str(tmp_path / "backup.zip"), "test"),
    )
    connection.commit()
    set_last_self_check({"created_at": "2026-05-01 15:00", "issues": ["Нет свежего архива"]})

    navigated: list[str] = []
    view = DashboardView(navigate=navigated.append)
    view.refresh()

    text = _visible_text(view)
    for expected in [
        "Профиль",
        "База",
        "Игроки: 1",
        "Турниры: 3",
        "Черновики: 1",
        "На проверке: 1",
        "Опубликованы: 1",
        "Контрольные заметки: 1",
        "Точки восстановления: 1",
        "Требует внимания",
        "Турнир на проверке",
        "Не заполнен клуб",
        "Нет свежего архива",
    ]:
        assert expected in text

    legacy_ascii_code = "E" + "BCK"
    legacy_cyrillic_code = "Е" + "ВСК"
    for forbidden in [legacy_ascii_code, legacy_cyrillic_code, "разряд", "норматив"]:
        assert forbidden not in text

    buttons = {button.text(): button for button in view.findChildren(__import__("PySide6.QtWidgets").QtWidgets.QPushButton)}
    for label in ["Рейтинг", "Турниры", "Игроки", "Импорт", "Отчеты", "Диагностика"]:
        assert label in buttons
        buttons[label].click()

    assert navigated == ["Рейтинг", "Турниры", "Игроки", "Импорт/Экспорт", "Отчеты", "Диагностика"]

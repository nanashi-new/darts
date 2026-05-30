from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


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


class TestCoachTaskFormData:
    def test_dataclass_fields(self) -> None:
        try:
            from app.ui.coach_task_dialog import CoachTaskFormData
        except Exception as exc:  # noqa: BLE001
            if _is_expected_headless_qt_failure(exc):
                pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
            raise

        data = CoachTaskFormData(
            title="Test task",
            description="desc",
            player_id=1,
            due_date="2025-01-01",
            priority="high",
            category="technique",
            status="open",
        )
        assert data.title == "Test task"
        assert data.player_id == 1
        assert data.priority == "high"
        assert data.status == "open"

    def test_optional_fields(self) -> None:
        try:
            from app.ui.coach_task_dialog import CoachTaskFormData
        except Exception as exc:  # noqa: BLE001
            if _is_expected_headless_qt_failure(exc):
                pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
            raise

        data = CoachTaskFormData(
            title="Minimal",
            description=None,
            player_id=None,
            due_date=None,
            priority="normal",
            category=None,
            status="open",
        )
        assert data.description is None
        assert data.player_id is None


class TestTrainingPlanFormData:
    def test_dataclass_fields(self) -> None:
        try:
            from app.ui.training_plan_dialog import TrainingPlanFormData
        except Exception as exc:  # noqa: BLE001
            if _is_expected_headless_qt_failure(exc):
                pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
            raise

        data = TrainingPlanFormData(
            title="Plan A",
            player_id=2,
            description="desc",
            goal="Improve doubles",
            start_date="2025-01-01",
            end_date="2025-02-01",
            status="active",
            exercises=[{"name": "doubles", "reps": 20}],
        )
        assert data.title == "Plan A"
        assert data.player_id == 2
        assert data.exercises == [{"name": "doubles", "reps": 20}]

    def test_optional_fields(self) -> None:
        try:
            from app.ui.training_plan_dialog import TrainingPlanFormData
        except Exception as exc:  # noqa: BLE001
            if _is_expected_headless_qt_failure(exc):
                pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
            raise

        data = TrainingPlanFormData(
            title="Minimal plan",
            player_id=1,
            description=None,
            goal=None,
            start_date=None,
            end_date=None,
            status="active",
            exercises=[],
        )
        assert data.description is None
        assert data.exercises == []


class TestCoachViewWidget:
    def test_coach_view_instantiation(self, tmp_path) -> None:
        _ensure_app()
        try:
            from app.db.database import get_connection
            from app.ui.coach_view import CoachView

            # Patch get_connection to use tmp DB
            import app.ui.coach_view as cv_module
            original_get_conn = cv_module.get_connection
            conn = get_connection(tmp_path / "test.db")
            cv_module.get_connection = lambda: conn  # type: ignore[assignment,misc]
            try:
                view = CoachView()
                assert view._tabs.count() == 3
                assert view._tabs.tabText(0) == "Задачи"
                assert view._tabs.tabText(1) == "Планы"
                assert view._tabs.tabText(2) == "Сводка"
            finally:
                cv_module.get_connection = original_get_conn
        except Exception as exc:  # noqa: BLE001
            if _is_expected_headless_qt_failure(exc):
                pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
            raise


class TestCoachTaskDialog:
    def test_dialog_instantiation(self, tmp_path) -> None:
        _ensure_app()
        try:
            from app.db.database import get_connection
            from app.ui.coach_task_dialog import CoachTaskDialog

            conn = get_connection(tmp_path / "test.db")
            dialog = CoachTaskDialog(connection=conn)
            assert dialog.windowTitle() == "Новая задача тренера"
        except Exception as exc:  # noqa: BLE001
            if _is_expected_headless_qt_failure(exc):
                pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
            raise


class TestTrainingPlanDialog:
    def test_dialog_instantiation(self, tmp_path) -> None:
        _ensure_app()
        try:
            from app.db.database import get_connection
            from app.ui.training_plan_dialog import TrainingPlanDialog

            conn = get_connection(tmp_path / "test.db")
            dialog = TrainingPlanDialog(connection=conn)
            assert dialog.windowTitle() == "Новый план тренировок"
        except Exception as exc:  # noqa: BLE001
            if _is_expected_headless_qt_failure(exc):
                pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
            raise

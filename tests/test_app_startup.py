from __future__ import annotations

import sys
import types


def test_app_main_uses_workspace_show(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))

    calls: list[str] = []

    class FakeApplication:
        def __init__(self, _args: list[str]) -> None:
            calls.append("app")

        def exec(self) -> int:
            calls.append("exec")
            return 0

    class FakeMainWindow:
        def show_workspace(self) -> None:
            calls.append("show_workspace")

    qt_widgets = types.ModuleType("PySide6.QtWidgets")
    qt_widgets.QApplication = FakeApplication
    pyside = types.ModuleType("PySide6")
    pyside.QtWidgets = qt_widgets
    main_window = types.ModuleType("app.ui.main_window")
    main_window.MainWindow = FakeMainWindow

    monkeypatch.setitem(sys.modules, "PySide6", pyside)
    monkeypatch.setitem(sys.modules, "PySide6.QtWidgets", qt_widgets)
    monkeypatch.setitem(sys.modules, "app.ui.main_window", main_window)
    monkeypatch.delitem(sys.modules, "app.__main__", raising=False)

    from app.__main__ import main

    assert main() == 0
    assert calls == ["app", "show_workspace", "exec"]

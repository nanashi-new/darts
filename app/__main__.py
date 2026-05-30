from __future__ import annotations

import logging
from pathlib import Path

from app.build_info import load_build_info
from app.runtime_paths import get_runtime_paths
from app.services.restore_points import process_pending_profile_action


def main() -> int:
    log_path = _configure_startup_logging()
    logging.info("Starting Darts Liga")
    logging.info("Runtime paths: %s", get_runtime_paths().to_dict())
    logging.info("Build info: %s", load_build_info().to_dict())
    pending_result = process_pending_profile_action()
    if pending_result is not None:
        logging.info("Processed pending profile action: %s", pending_result)

    try:
        from PySide6.QtWidgets import QApplication

        from app.settings import load_settings
        from app.ui.main_window import MainWindow
        from app.ui.theme import ThemeManager

        app = QApplication([])
        settings = load_settings()
        appearance = settings.get("appearance")
        theme = (
            str(appearance.get("theme", "light"))
            if isinstance(appearance, dict)
            else "light"
        )
        ThemeManager.apply_theme(app, theme)
        window = MainWindow()
        window.show_workspace()
        return app.exec()
    except Exception:
        logging.exception("Fatal startup error. See log at %s", log_path)
        raise


def _configure_startup_logging() -> Path:
    paths = get_runtime_paths()
    log_path = paths.logs_dir / "startup.log"
    logging.basicConfig(
        filename=str(log_path),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        force=True,
    )
    return log_path


if __name__ == "__main__":
    raise SystemExit(main())

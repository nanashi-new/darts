from __future__ import annotations

import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


APP_DIR_NAME = "Darts"
PROFILE_ROOT_ENV_VAR = "DARTS_PROFILE_ROOT"


@dataclass(frozen=True)
class RuntimePaths:
    profile_root: Path
    db_path: Path
    settings_path: Path
    logs_dir: Path
    exports_dir: Path
    restore_points_dir: Path
    diagnostics_dir: Path
    profile_backups_dir: Path
    import_profiles_path: Path
    player_match_rules_path: Path
    pending_action_path: Path

    def ensure_exists(self) -> "RuntimePaths":
        self.profile_root.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.restore_points_dir.mkdir(parents=True, exist_ok=True)
        self.diagnostics_dir.mkdir(parents=True, exist_ok=True)
        self.profile_backups_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.import_profiles_path.parent.mkdir(parents=True, exist_ok=True)
        self.player_match_rules_path.parent.mkdir(parents=True, exist_ok=True)
        self.pending_action_path.parent.mkdir(parents=True, exist_ok=True)
        return self

    def to_dict(self) -> dict[str, str]:
        return {key: str(value) for key, value in asdict(self).items()}


def get_runtime_paths() -> RuntimePaths:
    profile_root = _resolve_profile_root()
    paths = RuntimePaths(
        profile_root=profile_root,
        db_path=profile_root / "app.db",
        settings_path=profile_root / "settings.json",
        logs_dir=profile_root / "logs",
        exports_dir=profile_root / "exports",
        restore_points_dir=profile_root / "restore_points",
        diagnostics_dir=profile_root / "diagnostics",
        profile_backups_dir=profile_root.parent / f"{profile_root.name}_backups",
        import_profiles_path=profile_root / "import_profiles.json",
        player_match_rules_path=profile_root / "player_match_rules.json",
        pending_action_path=profile_root / "pending_action.json",
    )
    return paths.ensure_exists()


def get_default_profile_root() -> Path:
    return _resolve_profile_root()


def get_application_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parent


def get_bundled_resource_path(relative_path: str | Path) -> Path:
    relative = Path(relative_path)
    app_root = get_application_root()
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return app_root / "app" / relative
    return app_root / relative


def _resolve_profile_root() -> Path:
    override = os.environ.get(PROFILE_ROOT_ENV_VAR)
    if override:
        return Path(override).expanduser().resolve()
    if os.name == "nt":
        base_dir = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        if base_dir:
            root = Path(base_dir)
        else:
            root = Path.home() / "AppData" / "Roaming"
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return (root / APP_DIR_NAME).resolve()

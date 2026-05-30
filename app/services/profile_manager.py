from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProfileInfo:
    name: str
    path: Path
    db_exists: bool
    last_modified: str  # ISO format or empty


class ProfileManager:
    """Manages multiple isolated profiles (each with own DB, settings, etc.)."""

    def __init__(self, profiles_base_dir: Path) -> None:
        self._base_dir = profiles_base_dir
        self._registry_path = profiles_base_dir / "profiles.json"

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    @property
    def registry_path(self) -> Path:
        return self._registry_path

    def list_profiles(self) -> list[ProfileInfo]:
        """Scan base_dir for subdirectories that contain app.db or settings.json."""
        profiles: list[ProfileInfo] = []
        if not self._base_dir.is_dir():
            return profiles
        for entry in sorted(self._base_dir.iterdir()):
            if not entry.is_dir():
                continue
            db_path = entry / "app.db"
            settings_path = entry / "settings.json"
            if db_path.exists() or settings_path.exists():
                profiles.append(self._build_profile_info(entry))
        return profiles

    def create_profile(self, name: str) -> ProfileInfo:
        """Create new profile directory with name. Directory name = sanitized name."""
        dir_name = self._sanitize_name(name)
        if not dir_name:
            dir_name = "profile"
        profile_path = self._base_dir / dir_name
        # Ensure unique directory name
        counter = 1
        original = profile_path
        while profile_path.exists():
            profile_path = original.parent / f"{original.name}_{counter}"
            counter += 1
        profile_path.mkdir(parents=True, exist_ok=True)
        # Create subdirectories
        (profile_path / "logs").mkdir(exist_ok=True)
        (profile_path / "exports").mkdir(exist_ok=True)
        (profile_path / "restore_points").mkdir(exist_ok=True)
        (profile_path / "diagnostics").mkdir(exist_ok=True)
        # Create empty settings
        settings_path = profile_path / "settings.json"
        settings_path.write_text("{}", encoding="utf-8")
        # Register profile
        self._register_profile(profile_path)
        return self._build_profile_info(profile_path)

    def get_current_profile_name(self) -> str:
        """Return name of current active profile from registry (last_used)."""
        last_used = self.get_last_used_profile_path()
        if last_used is not None:
            return last_used.name
        return ""

    def get_last_used_profile_path(self) -> Path | None:
        """Read registry and return last used profile path, or None."""
        registry = self._read_registry()
        last_used = registry.get("last_used", "")
        if last_used:
            path = Path(last_used)
            if path.is_dir():
                return path
        return None

    def set_last_used_profile(self, profile_path: Path) -> None:
        """Update registry with last used profile path."""
        registry = self._read_registry()
        registry["last_used"] = str(profile_path.resolve())
        profiles_list: list[str] = registry.get("profiles", [])
        resolved = str(profile_path.resolve())
        if resolved not in profiles_list:
            profiles_list.append(resolved)
            registry["profiles"] = profiles_list
        self._write_registry(registry)

    def delete_profile(self, profile_path: Path) -> bool:
        """Delete profile directory. Returns False if it's the current active profile."""
        last_used = self.get_last_used_profile_path()
        if last_used is not None and last_used.resolve() == profile_path.resolve():
            return False
        if profile_path.is_dir():
            shutil.rmtree(profile_path)
        # Remove from registry
        registry = self._read_registry()
        profiles_list: list[str] = registry.get("profiles", [])
        resolved = str(profile_path.resolve())
        if resolved in profiles_list:
            profiles_list.remove(resolved)
            registry["profiles"] = profiles_list
        self._write_registry(registry)
        return True

    def _build_profile_info(self, path: Path) -> ProfileInfo:
        db_path = path / "app.db"
        db_exists = db_path.exists()
        last_modified = ""
        if db_exists:
            mtime = db_path.stat().st_mtime
            last_modified = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
        elif (path / "settings.json").exists():
            mtime = (path / "settings.json").stat().st_mtime
            last_modified = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
        return ProfileInfo(
            name=path.name,
            path=path,
            db_exists=db_exists,
            last_modified=last_modified,
        )

    def _sanitize_name(self, name: str) -> str:
        """Sanitize profile name to be a valid directory name."""
        sanitized = re.sub(r'[<>:"/\\|?*]', "_", name.strip())
        sanitized = sanitized.strip(". ")
        return sanitized

    def _register_profile(self, profile_path: Path) -> None:
        registry = self._read_registry()
        profiles_list: list[str] = registry.get("profiles", [])
        resolved = str(profile_path.resolve())
        if resolved not in profiles_list:
            profiles_list.append(resolved)
            registry["profiles"] = profiles_list
        self._write_registry(registry)

    def _read_registry(self) -> dict[str, Any]:
        if not self._registry_path.exists():
            return {"last_used": "", "profiles": []}
        try:
            text = self._registry_path.read_text(encoding="utf-8")
            data = json.loads(text)
            if isinstance(data, dict):
                return data  # type: ignore[return-value]
        except (json.JSONDecodeError, OSError):
            pass
        return {"last_used": "", "profiles": []}

    def _write_registry(self, registry: dict[str, Any]) -> None:
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._registry_path.write_text(
            json.dumps(registry, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from app.db.schema import SCHEMA_VERSION
from app.runtime_paths import get_bundled_resource_path


@dataclass(frozen=True)
class BuildInfo:
    version: str
    build_timestamp: str
    git_revision: str
    packaging_mode: str
    schema_version: str
    generated: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def load_build_info() -> BuildInfo:
    metadata_path = get_bundled_resource_path("resources/build_info.json")
    if metadata_path.exists():
        try:
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {}
        if isinstance(payload, dict):
            return BuildInfo(
                version=str(payload.get("version") or "1.0.0"),
                build_timestamp=str(payload.get("build_timestamp") or _dev_timestamp()),
                git_revision=str(payload.get("git_revision") or "unknown"),
                packaging_mode=str(payload.get("packaging_mode") or "packaged"),
                schema_version=str(payload.get("schema_version") or SCHEMA_VERSION),
                generated=True,
            )
    return BuildInfo(
        version="1.0.0",
        build_timestamp=_dev_timestamp(),
        git_revision="dev",
        packaging_mode="dev",
        schema_version=str(SCHEMA_VERSION),
        generated=False,
    )


def _dev_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

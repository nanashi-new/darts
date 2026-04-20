from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def main() -> int:
    req_file = pathlib.Path("requirements-pinned.txt")
    wheels_dir = pathlib.Path("vendor/wheels")
    manifest_path = wheels_dir / "manifest.json"

    requirements: dict[str, dict[str, str]] = {}
    for raw in req_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "==" not in line:
            raise SystemExit(f"Only pinned versions are supported: {line}")
        package, version = [part.strip() for part in line.split("==", 1)]
        requirements[normalize(package)] = {"package": package, "version": version}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_map = {normalize(item["package"]): item for item in manifest.get("entries", [])}
    errors: list[str] = []
    for normalized_name, expected in requirements.items():
        item = manifest_map.get(normalized_name)
        if item is None:
            errors.append(f"Manifest entry missing for {expected['package']}=={expected['version']}")
            continue
        if item.get("version") != expected["version"]:
            errors.append(
                f"Version mismatch for {expected['package']}: expected {expected['version']} got {item.get('version')}"
            )
            continue
        wheel_path = wheels_dir / item["filename"]
        if not wheel_path.exists():
            errors.append(f"Wheel not found: {wheel_path}")
            continue
        actual_hash = hashlib.sha256(wheel_path.read_bytes()).hexdigest()
        if actual_hash != item.get("sha256"):
            errors.append(
                f"Hash mismatch for {item['filename']}: expected {item.get('sha256')} got {actual_hash}"
            )

    if errors:
        for error in errors:
            print(error)
        return 1

    print("Offline wheel manifest validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

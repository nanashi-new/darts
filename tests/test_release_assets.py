from __future__ import annotations

from pathlib import Path


def test_release_scripts_and_spec_exist() -> None:
    project_root = Path(__file__).resolve().parent.parent

    expected_paths = [
        project_root / "pyinstaller.release.spec",
        project_root / "scripts" / "BUILD_RELEASE.bat",
        project_root / "scripts" / "RUN_APP.bat",
        project_root / "scripts" / "PREPARE_OFFLINE_DEPS.bat",
        project_root / "scripts" / "SMOKE_TEST.bat",
        project_root / "scripts" / "RESET_APP_DATA.bat",
        project_root / "scripts" / "PACK_RELEASE.bat",
        project_root / "scripts" / "generate_build_info.py",
        project_root / "scripts" / "validate_wheels_manifest.py",
    ]

    for path in expected_paths:
        assert path.exists(), path

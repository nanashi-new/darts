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

    assert (project_root / "installer" / "DartsLiga.iss").exists()


def test_release_spec_includes_qt_print_support() -> None:
    project_root = Path(__file__).resolve().parent.parent
    spec_path = project_root / "pyinstaller.release.spec"
    content = spec_path.read_text(encoding="utf-8")

    assert "PySide6.QtPrintSupport" in content


def test_release_artifacts_use_darts_liga_names() -> None:
    project_root = Path(__file__).resolve().parent.parent
    active_files = [
        project_root / "pyinstaller.release.spec",
        project_root / "pyinstaller.spec",
        project_root / "scripts" / "BUILD_RELEASE.bat",
        project_root / "scripts" / "RUN_APP.bat",
        project_root / "scripts" / "SMOKE_TEST.bat",
        project_root / "scripts" / "PACK_RELEASE.bat",
        project_root / "scripts" / "BUILD_INSTALLER.bat",
        project_root / "installer" / "DartsLiga.iss",
        project_root / "10_RELEASE_CHECKLIST.md",
        project_root / "README.md",
    ]

    combined = "\n".join(path.read_text(encoding="utf-8") for path in active_files)

    assert "DartsLiga.exe" in combined
    assert "DartsLiga-release.zip" in combined
    assert "DartsLiga-Setup.exe" in combined
    assert "DartsRatingEBCK" not in combined
    assert "Darts Rating EBCK" not in combined

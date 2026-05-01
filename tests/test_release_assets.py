from __future__ import annotations

from pathlib import Path


def _priority_rows() -> dict[int, str]:
    project_root = Path(__file__).resolve().parent.parent
    priority_path = project_root / "planning" / "00_PRIORITY.md"
    rows: dict[int, str] = {}
    for line in priority_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) == 5 and cells[0].isdigit():
            rows[int(cells[0])] = cells[2]
    return rows


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


def test_dev_requirements_include_release_check_tools() -> None:
    project_root = Path(__file__).resolve().parent.parent
    dev_requirements = (project_root / "requirements-dev.txt").read_text(encoding="utf-8")
    pinned_requirements = (project_root / "requirements-pinned.txt").read_text(encoding="utf-8")

    assert "-r requirements.txt" in dev_requirements
    assert "mypy" in dev_requirements
    assert "pytest" in dev_requirements
    assert "mypy" not in pinned_requirements
    assert "pytest" not in pinned_requirements


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
    legacy_code = "E" + "BCK"
    assert f"{'Darts'}{'Rating'}{legacy_code}" not in combined
    assert f"{'Darts'} Rating {legacy_code}" not in combined


def test_release_preflight_p0_requirements_are_closed_and_legacy_brand_absent() -> None:
    project_root = Path(__file__).resolve().parent.parent
    priority_rows = _priority_rows()

    for order in range(7, 14):
        assert priority_rows[order] == "done"

    active_roots = [project_root / "app", project_root / "tests", project_root / "planning"]
    legacy_code = "E" + "BCK"
    forbidden_terms = [
        f"{'Darts'}{'Rating'}{legacy_code}",
        f"{'Darts'} Rating {legacy_code}",
        legacy_code,
    ]
    matches: list[str] = []
    for root in active_roots:
        for path in root.rglob("*"):
            if path.is_dir() or "planning/archive" in path.as_posix():
                continue
            if path.suffix.lower() not in {".py", ".md", ".txt", ".iss", ".bat", ".spec"}:
                continue
            content = path.read_text(encoding="utf-8", errors="ignore")
            for term in forbidden_terms:
                if term in content:
                    matches.append(f"{path.relative_to(project_root)}: {term}")

    assert matches == []

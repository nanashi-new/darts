from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import pytest

from app.db.database import get_connection
from app.db.repositories import PlayerRepository


pytestmark = pytest.mark.integration


def test_runtime_paths_use_profile_override(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))

    from app.runtime_paths import get_runtime_paths

    paths = get_runtime_paths()

    assert paths.profile_root == tmp_path / "profile"
    assert paths.db_path == paths.profile_root / "app.db"
    assert paths.settings_path == paths.profile_root / "settings.json"
    assert paths.logs_dir.is_dir()
    assert paths.exports_dir.is_dir()
    assert paths.restore_points_dir.is_dir()
    assert paths.diagnostics_dir.is_dir()


def test_load_build_info_has_dev_fallback() -> None:
    from app.build_info import load_build_info

    info = load_build_info()

    assert info.version
    assert info.packaging_mode
    assert info.schema_version


def test_create_restore_point_persists_backup_and_metadata(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    connection = get_connection()
    PlayerRepository(connection).create(
        {
            "last_name": "Backup",
            "first_name": "Case",
            "middle_name": None,
            "birth_date": None,
            "gender": None,
            "coach": None,
            "club": None,
            "notes": None,
        }
    )

    from app.services.restore_points import create_restore_point, list_restore_points

    record = create_restore_point(
        connection=connection,
        title="Before risky operation",
        reason="tests",
        source="tests",
    )

    assert Path(record.file_path).exists()
    persisted = list_restore_points(connection=connection)
    assert persisted
    assert persisted[0].reason == "tests"
    assert persisted[0].title == "Before risky operation"


def test_self_check_reports_missing_norms_template(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    monkeypatch.setenv("NORMS_XLSX_PATH", str(tmp_path / "missing" / "norms.xlsx"))
    connection = get_connection()

    from app.services import diagnostics

    monkeypatch.setattr(
        diagnostics,
        "get_bundled_resource_path",
        lambda relative_path: tmp_path / "missing-template.bin",
    )

    report = diagnostics.run_self_check(connection=connection)

    assert report.issues
    assert any(issue.code == "norms.unavailable" for issue in report.issues)


def test_export_diagnostic_bundle_contains_expected_files(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DARTS_PROFILE_ROOT", str(tmp_path / "profile"))
    connection = get_connection()

    from app.services.diagnostics import export_diagnostic_bundle, run_self_check

    report = run_self_check(connection=connection)
    bundle = export_diagnostic_bundle(connection=connection, self_check=report)

    assert Path(bundle.bundle_path).exists()
    with ZipFile(bundle.bundle_path) as archive:
        names = set(archive.namelist())

    assert "build_info.json" in names
    assert "self_check.json" in names
    assert "runtime_paths.json" in names

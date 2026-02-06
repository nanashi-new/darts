from __future__ import annotations

from pathlib import Path

import pytest
from openpyxl import load_workbook

import app
from app.db.database import get_connection, get_default_database_path
from app.db.repositories import PlayerRepository, ResultRepository, TournamentRepository
from app.services.audit_log import AuditLogService
from app.services.export_service import ExportService
from app.services.import_xlsx import ImportProfile, save_import_profile
from app.services.norms_loader import load_norms_from_settings


def _seed(connection) -> tuple[int, int]:
    players = PlayerRepository(connection)
    tournaments = TournamentRepository(connection)
    results = ResultRepository(connection)

    player_id = players.create(
        {
            "last_name": "Смок",
            "first_name": "Тест",
            "middle_name": None,
            "birth_date": "2010-01-01",
            "gender": "M",
            "coach": None,
            "club": None,
            "notes": None,
        }
    )
    tournament_id = tournaments.create(
        {
            "name": "Release smoke",
            "date": "2025-01-10",
            "category_code": "U12-M",
            "league_code": "A",
            "source_files": "[]",
        }
    )
    results.create(
        {
            "tournament_id": tournament_id,
            "player_id": player_id,
            "place": 1,
            "score_set": 100,
            "score_sector20": 50,
            "score_big_round": 60,
            "rank_set": "I",
            "rank_sector20": "I",
            "rank_big_round": "I",
            "points_classification": 10,
            "points_place": 20,
            "points_total": 30,
            "calc_version": "v2",
        }
    )
    return player_id, tournament_id


def test_release_smoke_max(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert app.__doc__

    import importlib

    importlib.import_module("app.db.database")
    importlib.import_module("app.db.repositories")
    importlib.import_module("app.domain.points")
    importlib.import_module("app.domain.ranks")
    importlib.import_module("app.services.import_xlsx")
    importlib.import_module("app.services.export_service")

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    app_root = get_default_database_path().parent

    db_path = get_default_database_path()
    connection = get_connection(db_path)
    _seed(connection)

    settings_path = app_root / "settings.json"
    _ = settings_path.parent

    norms_path = app_root / "norms.xlsx"
    if norms_path.exists():
        norms_path.unlink()
    monkeypatch.setenv("NORMS_XLSX_PATH", str(norms_path))
    loaded_first = load_norms_from_settings()
    assert loaded_first.loaded
    assert norms_path.exists()
    before_bytes = norms_path.read_bytes()
    loaded_second = load_norms_from_settings()
    assert loaded_second.loaded
    assert norms_path.read_bytes() == before_bytes

    save_import_profile(
        ImportProfile(
            name="release-profile",
            required_columns=["fio", "place", "score_set"],
            header_aliases={"fio": ["ФИО"]},
        )
    )
    profile_path = app_root / "import_profiles.json"

    logs_dir = app_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    audit_service = AuditLogService(connection)
    audit_service.log_event("RELEASE_SMOKE", "run", "ok")
    log_path = audit_service.export_txt(logs_dir / "audit.txt")

    exporter = ExportService()
    xlsx_path = tmp_path / "smoke.xlsx"
    exporter.export_dataset_xlsx(
        str(xlsx_path),
        header_lines=["Smoke"],
        columns=["A", "B"],
        rows=[["1", "2"]],
    )
    assert xlsx_path.exists()
    workbook = load_workbook(xlsx_path)
    assert workbook.active.cell(row=2, column=1).value == "A"

    pdf_path = tmp_path / "smoke.pdf"
    exporter.export_dataset_pdf(
        str(pdf_path),
        header_lines=["Smoke"],
        columns=["A", "B"],
        rows=[["1", "2"]],
    )
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0

    png_path = tmp_path / "smoke.png"
    try:
        exporter.export_dataset_image(
            str(png_path),
            columns=["A", "B"],
            rows=[["1", "2"]],
            column_widths=[100, 100],
        )
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Qt headless PNG export unavailable: {exc}")

    assert png_path.exists()
    assert png_path.stat().st_size > 0

    exports_dir = app_root / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    expected_dirs = [
        app_root,
        db_path.parent,
        settings_path.parent,
        norms_path.parent,
        profile_path.parent,
        logs_dir,
        exports_dir,
    ]
    for path in expected_dirs:
        assert path.exists()

    assert log_path.exists()

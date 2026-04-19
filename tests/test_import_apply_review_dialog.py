from __future__ import annotations

import os

import pytest

from app.domain.rating import RatingImpactRow, RatingSnapshotRow
from app.services.import_review import ImportRatingImpactPreview
from app.services.league_transfer import LeagueTransferPreview, LeagueTransferPreviewRow
from app.services.import_xlsx import ImportApplyReport


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytestmark = pytest.mark.release_smoke


def _is_expected_headless_qt_failure(exc: Exception) -> bool:
    message = str(exc).lower()
    markers = (
        "libgl.so.1",
        "libegl.so.1",
        "libxkbcommon.so.0",
        "could not load the qt platform plugin",
        "no qt platform plugin could be initialized",
        "qt.qpa.plugin",
        "xcb",
        "offscreen",
    )
    return isinstance(exc, (ImportError, OSError, RuntimeError)) and any(marker in message for marker in markers)


def _ensure_app() -> object:
    try:
        from PySide6.QtWidgets import QApplication
    except Exception as exc:  # noqa: BLE001
        if isinstance(exc, ModuleNotFoundError):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_import_apply_review_dialog_shows_summary_warnings_and_rating_impact() -> None:
    try:
        _ensure_app()
        from app.ui.import_apply_review_dialog import ImportApplyReviewDialog
    except Exception as exc:  # noqa: BLE001
        if isinstance(exc, ModuleNotFoundError):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        if _is_expected_headless_qt_failure(exc):
            pytest.skip(f"Qt headless UI smoke unavailable: {exc}")
        raise

    dialog = ImportApplyReviewDialog(
        apply_report=ImportApplyReport(
            tournament_id=17,
            tournament_name="Spring Cup",
            tournament_status="draft",
            has_draft_changes=True,
            imported_rows=2,
            skipped_rows=1,
            total_rows=3,
            warnings=["Missing norms file"],
            norms_loaded=False,
            source_files=["/tmp/import.xlsx"],
            operation_group_id="op-import-dialog",
            files_processed=1,
            tables_processed=1,
            rows_read=3,
            players_created=1,
            players_reused=1,
            players_matched_manually=1,
        ),
        rating_preview=ImportRatingImpactPreview(
            available=True,
            reason=None,
            before_rows=[
                RatingSnapshotRow(player_id=1, place=1, fio="Adams Alice", points=100, tournaments_count=1),
            ],
            after_rows=[
                RatingSnapshotRow(player_id=2, place=1, fio="Brown Bob", points=120, tournaments_count=1),
                RatingSnapshotRow(player_id=1, place=2, fio="Adams Alice", points=100, tournaments_count=1),
            ],
            rows=[
                RatingImpactRow(
                    player_id=2,
                    fio="Brown Bob",
                    old_place=None,
                    new_place=1,
                    place_delta=None,
                    old_points=0,
                    new_points=120,
                    points_delta=120,
                ),
                RatingImpactRow(
                    player_id=1,
                    fio="Adams Alice",
                    old_place=1,
                    new_place=2,
                    place_delta=-1,
                    old_points=100,
                    new_points=100,
                    points_delta=0,
                ),
            ],
        ),
        league_preview=LeagueTransferPreview(
            available=True,
            reason=None,
            rows=[
                LeagueTransferPreviewRow(
                    player_id=2,
                    fio="Brown Bob",
                    from_league_code="FIRST",
                    to_league_code="PREMIER",
                )
            ],
        ),
    )

    assert dialog.summary_list.count() >= 4
    summary_text = "\n".join(
        dialog.summary_list.item(index).text() for index in range(dialog.summary_list.count())
    )
    assert "Spring Cup" in summary_text
    assert "3" in summary_text
    assert "1" in summary_text
    assert dialog.warnings_list.count() == 2
    assert dialog.impact_table.rowCount() == 2
    assert dialog.impact_table.columnCount() == 7
    assert dialog.league_table.rowCount() == 1
    assert dialog.leave_button.text() == "Оставить draft"
    assert dialog.publish_button.text() == "Опубликовать сейчас"

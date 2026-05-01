from __future__ import annotations

from pathlib import Path


def test_customer_requirements_reference_has_no_stale_p0_alignment_statuses() -> None:
    project_root = Path(__file__).resolve().parent.parent
    reference_path = (
        project_root
        / "planning"
        / "reference"
        / "customer-requirements"
        / "2026-02-02-rating-system-requirements-approved.md"
    )
    content = reference_path.read_text(encoding="utf-8")

    stale_markers = [
        "in progress P0",
        "in progress P0/P1",
        "planned P0",
        "partial/done",
        "tested P0",
    ]
    for marker in stale_markers:
        assert marker not in content


def test_customer_requirements_reference_keeps_future_items_explicit() -> None:
    project_root = Path(__file__).resolve().parent.parent
    reference_path = (
        project_root
        / "planning"
        / "reference"
        / "customer-requirements"
        / "2026-02-02-rating-system-requirements-approved.md"
    )
    content = reference_path.read_text(encoding="utf-8")

    assert "CSV/Word/QR экспорт | planned/optional" in content
    assert "league-season-transitions-v2.md" in content
    assert "faq-user-guide" in content

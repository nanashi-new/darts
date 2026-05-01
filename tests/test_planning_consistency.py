from __future__ import annotations

import re
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _priority_rows() -> list[dict[str, str]]:
    priority_path = _project_root() / "planning" / "00_PRIORITY.md"
    rows: list[dict[str, str]] = []
    for line in priority_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or "[/" in line or "---" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 5 or not cells[0].isdigit():
            continue
        task_match = re.search(r"\((tasks/[^)]+)\)", cells[3])
        if task_match is None:
            continue
        rows.append(
            {
                "order": cells[0],
                "task": cells[1],
                "status": cells[2],
                "task_path": task_match.group(1),
            }
        )
    return rows


def _task_status(task_path: str) -> str | None:
    content = (_project_root() / "planning" / task_path).read_text(encoding="utf-8")
    match = re.search(r"^Статус:\s*([^\n]+)", content, flags=re.MULTILINE)
    if match is None:
        return None
    return match.group(1).strip().strip("*").lower()


def test_done_priority_tasks_have_done_task_files() -> None:
    mismatches: list[str] = []
    for row in _priority_rows():
        if row["status"] != "done":
            continue
        status = _task_status(row["task_path"])
        if status != "done":
            mismatches.append(
                f"{row['order']}. {row['task']} -> {row['task_path']} has status {status!r}"
            )

    assert mismatches == []


def test_p0_customer_requirements_automation_and_release_readiness_are_done() -> None:
    rows_by_order = {int(row["order"]): row for row in _priority_rows()}

    for order in range(7, 14):
        assert rows_by_order[order]["status"] == "done"
        assert _task_status(rows_by_order[order]["task_path"]) == "done"

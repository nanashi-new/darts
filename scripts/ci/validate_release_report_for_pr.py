#!/usr/bin/env python3
"""Validate that release PR includes an updated manual release report."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

REQUIRED_SECTIONS = ("import", "recalc", "export", "merge", "audit")
REPORT_PATTERN = re.compile(r"^docs/artifacts/release-manual-run-.*\.md$")


def run(*args: str) -> str:
    return subprocess.check_output(args, text=True).strip()


def changed_files(base_ref: str, head_ref: str) -> list[str]:
    out = run("git", "diff", "--name-only", f"{base_ref}...{head_ref}")
    return [line for line in out.splitlines() if line]


def assert_report_content(path: Path) -> None:
    text = path.read_text(encoding="utf-8").lower()

    missing_sections = [s for s in REQUIRED_SECTIONS if s not in text]
    if missing_sections:
        raise SystemExit(
            f"{path}: missing required sections/keywords: {', '.join(missing_sections)}"
        )

    if "[" not in text or "](" not in text:
        raise SystemExit(
            f"{path}: expected markdown links to results in mandatory sections"
        )


def main() -> None:
    event_name = os.getenv("GITHUB_EVENT_NAME", "")
    if event_name != "pull_request":
        print("Skip: check applies only to pull_request events.")
        return

    base_ref = os.getenv("GITHUB_BASE_REF", "")
    if not (base_ref == "release" or base_ref.startswith("release/")):
        print(f"Skip: base branch '{base_ref}' is not a release branch.")
        return

    base_sha = os.environ["GITHUB_BASE_SHA"]
    head_sha = os.environ["GITHUB_SHA"]
    files = changed_files(base_sha, head_sha)

    report_files = [f for f in files if REPORT_PATTERN.match(f)]
    if not report_files:
        raise SystemExit(
            "Release PR must update/add a manual run report: "
            "docs/artifacts/release-manual-run-*.md"
        )

    for rel_path in report_files:
        assert_report_content(Path(rel_path))

    print("Release manual run report validation passed.")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(exc.output, file=sys.stderr)
        raise

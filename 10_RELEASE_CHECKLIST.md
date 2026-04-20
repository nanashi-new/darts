# 10 - Release Checklist

Current release target: minimal finished desktop v1 from `feature/adult-league-rating-transitions`.

Latest packaged verification artifact:
- [`docs/artifacts/release-manual-run-2026-04-20-packaged-finish.md`](docs/artifacts/release-manual-run-2026-04-20-packaged-finish.md)

Latest packaged outputs:
- `dist/DartsRatingEBCK.exe`
- `release/DartsRatingEBCK-release.zip`

## Code and test gates

- [x] `pytest -q` passes on the current branch
- [x] `python -m py_compile` over `app/` and `tests/` passes
- [x] diagnostics/runtime/recovery tests pass
- [x] training/context/dashboard regressions remain green
- [x] dependency installation uses `requirements-pinned.txt`
- [x] offline wheel manifest validation is part of `scripts/BUILD_RELEASE.bat`

## Packaging gates

- [x] one-file PyInstaller spec exists: `pyinstaller.release.spec`
- [x] build metadata is generated before packaged build
- [x] packaged artifact is produced by `scripts/BUILD_RELEASE.bat`
- [x] packaged artifact path is printed by the build script
- [x] mutable user data stays outside the exe via runtime paths

## Clean-profile smoke gates

- [x] packaged app starts with a fresh `DARTS_PROFILE_ROOT`
- [x] first run creates `app.db`
- [x] first run creates `settings.json`
- [x] first run materializes `norms.xlsx`
- [x] first run writes `logs/startup.log`
- [x] second packaged run succeeds on the same profile
- [x] diagnostics/runtime metadata is available to the UI layer and included in the diagnostic bundle flow

## Recovery and diagnostics gates

- [x] restore points are persisted in SQLite and on disk
- [x] dangerous operations create restore points
- [x] safe reset is queued and processed on restart
- [x] diagnostic bundle export exists
- [x] self-check exists and reports issues

## Release scripts

- [x] `scripts/BUILD_RELEASE.bat`
- [x] `scripts/PREPARE_OFFLINE_DEPS.bat`
- [x] `scripts/RUN_APP.bat`
- [x] `scripts/SMOKE_TEST.bat`
- [x] `scripts/RESET_APP_DATA.bat`
- [x] `scripts/PACK_RELEASE.bat`

## Decision

Minimal finished v1 is release-ready on the current branch.

Deferred by choice, not by release blocker:
- attachments
- tags
- custom fields
- installer
- branding/theme customization
- advanced workspace presets and table-geometry persistence

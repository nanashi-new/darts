# 10 - Release Checklist

Active execution order lives in [`planning/00_PRIORITY.md`](planning/00_PRIORITY.md).
Use this file only as the release gate checklist.

Current release target: `Дартс Лига` desktop v1.1 from `feature/darts-liga-no-evsk`.

Latest packaged verification artifact:
- [`planning/archive/release-artifacts/release-manual-run-2026-04-20-packaged-finish.md`](planning/archive/release-artifacts/release-manual-run-2026-04-20-packaged-finish.md)

Expected release outputs:
- one-file executable: `dist/DartsLiga.exe`
- ZIP bundle: `release/DartsLiga-release.zip`
- Windows installer: `release/DartsLiga-Setup.exe`

## Code and test gates

- [x] `pytest -q` passes on the current branch
- [x] `python -m mypy app` passes
- [x] `python -m py_compile` over `app/` and `tests/` passes
- [x] UI smoke tests confirm Russian top-level tabs and no placeholder text
- [x] UI Russian text tests confirm visible app strings are localized
- [x] diagnostics/runtime/recovery tests pass
- [x] dependency installation uses `requirements-pinned.txt`
- [x] offline wheel manifest validation is part of `scripts/BUILD_RELEASE.bat`

## Packaging gates

- [x] one-file PyInstaller spec exists: `pyinstaller.release.spec`
- [x] build metadata is generated before packaged build
- [x] packaged artifact is produced by `scripts/BUILD_RELEASE.bat`
- [x] packaged artifact path is printed by the build script
- [x] mutable user data stays outside the exe via runtime paths
- [x] Inno Setup installer script exists: `installer/DartsLiga.iss`
- [x] installer build script exists: `scripts/BUILD_INSTALLER.bat`
- [x] ZIP bundle remains available as fallback packaging

## Clean-profile smoke gates

- [x] packaged app starts with a fresh `DARTS_PROFILE_ROOT`
- [x] first run creates `app.db`
- [x] first run creates `settings.json`
- [x] first run writes `logs/startup.log`
- [x] second packaged run succeeds on the same profile
- [x] diagnostics/runtime metadata is available to the UI layer and included in the diagnostic bundle flow

## Installer gates

- [ ] `scripts\BUILD_INSTALLER.bat` produces `release\DartsLiga-Setup.exe`
- [ ] installer UI is Russian
- [ ] installed app starts from Start menu shortcut
- [ ] optional desktop shortcut works
- [ ] uninstall removes the installed executable but leaves user profile data intact

## Release scripts

- [x] `scripts/BUILD_RELEASE.bat`
- [x] `scripts/PREPARE_OFFLINE_DEPS.bat`
- [x] `scripts/RUN_APP.bat`
- [x] `scripts/SMOKE_TEST.bat`
- [x] `scripts/RESET_APP_DATA.bat`
- [x] `scripts/PACK_RELEASE.bat`
- [x] `scripts/BUILD_INSTALLER.bat`

## Decision

The zip/exe fallback release is ready after the checked gates above. The Windows installer release remains blocked until the unchecked installer gates are verified on a machine with Inno Setup.

## Local Run - 2026-04-30

- Passed: `pytest -q` -> `142 passed, 14 deselected, 14 subtests passed`.
- Passed: `python -m compileall -q app tests`.
- Passed: `scripts\BUILD_RELEASE.bat` with `.venv\Scripts` first in `PATH`; produced `dist\DartsLiga.exe`.
- Passed: `scripts\SMOKE_TEST.bat`; clean profile `DartsSmoke_180778817` created `app.db`, `settings.json`, `logs/startup.log`, and second packaged run succeeded.
- Passed: `scripts\PACK_RELEASE.bat`; produced `release\DartsLiga-release.zip`.
- Blocked: `scripts\BUILD_INSTALLER.bat` because Inno Setup compiler `ISCC.exe` is not installed; script now returns `LASTEXITCODE=1` for this blocker.
- Manual gate still open: visual pass for «Турниры» at 1920x1080/1366x768 and reduced window.

## Local Run - 2026-05-01

- Passed: `pytest -q` -> `153 passed, 14 deselected, 14 subtests passed`.
- Passed: `python -m mypy app` -> `Success: no issues found in 38 source files`.
- Passed: `python -m compileall -q app tests`.
- Passed: targeted rating/snapshot/import preview gate -> `34 passed`.
- Dev tooling is now documented in `requirements-dev.txt`; release/offline dependencies remain in `requirements-pinned.txt`.
- Passed: `scripts\BUILD_RELEASE.bat`; produced fresh `dist\DartsLiga.exe`.
- Passed: `scripts\SMOKE_TEST.bat`; internal smoke tests passed (`12 passed`) and clean profile `DartsSmoke_1135032382` started twice.
- Passed: `scripts\PACK_RELEASE.bat`; produced fresh `release\DartsLiga-release.zip`.
- Blocked: `scripts\BUILD_INSTALLER.bat` because Inno Setup compiler `ISCC.exe` is not installed.

Deferred by choice, not by release blocker:
- attachments
- tags
- custom fields
- branding/theme customization
- advanced workspace presets and table-geometry persistence

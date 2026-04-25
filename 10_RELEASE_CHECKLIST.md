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

- [ ] `pytest -q` passes on the current branch
- [ ] `python -m mypy app` passes
- [ ] `python -m py_compile` over `app/` and `tests/` passes
- [ ] UI smoke tests confirm Russian top-level tabs and no placeholder text
- [ ] UI Russian text tests confirm visible app strings are localized
- [ ] diagnostics/runtime/recovery tests pass
- [ ] dependency installation uses `requirements-pinned.txt`
- [ ] offline wheel manifest validation is part of `scripts/BUILD_RELEASE.bat`

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

- [ ] packaged app starts with a fresh `DARTS_PROFILE_ROOT`
- [ ] first run creates `app.db`
- [ ] first run creates `settings.json`
- [ ] first run writes `logs/startup.log`
- [ ] second packaged run succeeds on the same profile
- [ ] diagnostics/runtime metadata is available to the UI layer and included in the diagnostic bundle flow

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

The branch is ready for release only after the unchecked gates above are verified on Windows.

Deferred by choice, not by release blocker:
- attachments
- tags
- custom fields
- branding/theme customization
- advanced workspace presets and table-geometry persistence

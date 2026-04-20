# 11 - Release Test Run

## Latest packaged finish pass

- Date: 2026-04-20
- Branch: `feature/adult-league-rating-transitions`
- Base commit before final close-out commit: `a9af253`
- Environment: local Windows workstation, Python 3.13, one-file PyInstaller build
- Main artifact: `dist/DartsRatingEBCK.exe`
- Packed bundle: `release/DartsRatingEBCK-release.zip`
- Detailed report: [`artifacts/release-manual-run-2026-04-20-packaged-finish.md`](artifacts/release-manual-run-2026-04-20-packaged-finish.md)

## Commands executed

### Functional regression

```powershell
pytest -q
```

Expected result for this finish pass:
- all tests green
- Qt smoke tests may be skipped only in headless situations

### Bytecode verification

```powershell
Get-ChildItem app -Recurse -Filter *.py | ForEach-Object { python -m py_compile $_.FullName }
Get-ChildItem tests -Recurse -Filter *.py | ForEach-Object { python -m py_compile $_.FullName }
```

### One-file release build

```powershell
cmd /c scripts\BUILD_RELEASE.bat
```

Expected result:
- validates pinned requirements
- validates offline wheel manifest when `vendor/wheels` is present
- generates `build/build_info.json`
- produces `dist/DartsRatingEBCK.exe`

### Packaged clean-profile smoke

```powershell
cmd /c scripts\SMOKE_TEST.bat
```

Expected result:
- packaged app starts with a fresh `DARTS_PROFILE_ROOT`
- `app.db`, `settings.json`, `norms.xlsx`, and `logs/startup.log` are created
- second run also succeeds

### Release bundle

```powershell
cmd /c scripts\PACK_RELEASE.bat
```

Expected result:
- produces `release/DartsRatingEBCK-release.zip`

## Acceptance criteria for release close-out

- `pytest -q` passes
- `BUILD_RELEASE.bat` produces the one-file exe
- `SMOKE_TEST.bat` passes on a clean profile
- release docs point to the packaged finish-pass artifact
- checklist in `10_RELEASE_CHECKLIST.md` is fully green

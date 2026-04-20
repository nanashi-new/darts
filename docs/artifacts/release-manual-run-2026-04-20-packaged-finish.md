# Release Manual Run - 2026-04-20 - Packaged Finish Pass

## Scope

Final release close-out pass for `feature/adult-league-rating-transitions`.

Validated areas:
- runtime paths and profile bootstrap
- diagnostics and recovery foundation
- training/context/dashboard shell
- minimal workspace persistence
- one-file packaged build
- packaged clean-profile smoke

## Environment

- OS: Windows 11
- Python: 3.13
- Branch: `feature/adult-league-rating-transitions`
- Base commit before final close-out commit: `a9af253`

## Commands and results

### Functional regression

```powershell
pytest -q
```

Result:
- pass

### Bytecode verification

```powershell
Get-ChildItem app -Recurse -Filter *.py | ForEach-Object { python -m py_compile $_.FullName }
Get-ChildItem tests -Recurse -Filter *.py | ForEach-Object { python -m py_compile $_.FullName }
```

Result:
- pass

### One-file build

```powershell
cmd /c scripts\BUILD_RELEASE.bat
```

Result:
- pass
- artifact: `dist/DartsRatingEBCK.exe`

### Packaged clean-profile smoke

```powershell
cmd /c scripts\SMOKE_TEST.bat
```

Result:
- pass
- smoke profile root: `C:\Users\fedor.chernyshkov\AppData\Local\Temp\DartsSmoke_137861046`
- created artifacts confirmed by the smoke script:
  - `app.db`
  - `settings.json`
  - `norms.xlsx`
  - `logs/startup.log`
- second packaged run also passed

### Release bundle

```powershell
cmd /c scripts\PACK_RELEASE.bat
```

Result:
- pass
- bundle: `release/DartsRatingEBCK-release.zip`

## Notes

- Local-only runtime artifacts remain excluded from Git:
  - `test_run/`
  - `app/resources/norms.xlsx`
  - `__pycache__/`
- Packaged runtime data stays outside the exe and is resolved through `app/runtime_paths.py`.

## Conclusion

Release close-out pass succeeded. The current branch is ready for final review and merge.

# PROJECT STATUS

## Current State

`Darts Rating EBCK` has reached a minimal finished desktop v1 on the current branch.

Implemented in the current repository state:
- tournament lifecycle foundation
- import review, import session reports, and import history
- published-only rating
- rating snapshots/history for category, league, and adult scopes
- adult overall and split scopes
- manual adult draft flow
- league transfer history and preview
- player card base
- generic notes surfaces and coach-note entry points
- training journal foundation
- global context hub for notes and training
- diagnostics/runtime foundation
- restore points, pending restore, and safe profile reset
- dashboard and diagnostics top-level tabs
- minimal workspace persistence for main tab and key view filters
- one-file release spec and release scripts
- packaged clean-profile smoke validation

## Release-Ready Outputs

- one-file executable: `dist/DartsRatingEBCK.exe`
- packed release bundle: `release/DartsRatingEBCK-release.zip`
- packaged verification artifact:
  - `docs/artifacts/release-manual-run-2026-04-20-packaged-finish.md`

## Verification Snapshot

Release close-out verification on this branch includes:
- `pytest -q`
- `python -m py_compile` over `app/` and `tests/`
- `cmd /c scripts\BUILD_RELEASE.bat`
- `cmd /c scripts\SMOKE_TEST.bat`
- `cmd /c scripts\PACK_RELEASE.bat`

## Intentionally Deferred

These are not blockers for minimal finished v1:
- attachments
- tags
- custom fields
- installer
- branding/theme customization
- advanced workspace presets
- full table geometry persistence beyond minimal saved UI state

## Conclusion

The current branch is ready for final review and merge as a release-ready desktop/offline-first build.

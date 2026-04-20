# Release Manual Run — 2026-04-20 Finish Pass

## Scope

Focused finish-pass verification after adding:
- runtime paths and build metadata
- diagnostics/self-check/restore points
- release scripts and one-file spec
- training journal
- context hub
- dashboard

## Automated Verification

- `pytest -q`
  - result: `88 passed, 20 skipped`
- `python -m py_compile` across `app/` and `tests/`
  - result: passed

## Focused Areas Confirmed

- import/rating/adult/league/player-card regressions still green
- new runtime/diagnostics tests green
- new training journal tests green
- release asset presence tests green

## Remaining Manual Follow-Up

Still recommended before final release sign-off:
- run `scripts/BUILD_RELEASE.bat`
- launch packaged one-file exe on a clean Windows profile
- capture packaged smoke output and attach it as a follow-up artifact

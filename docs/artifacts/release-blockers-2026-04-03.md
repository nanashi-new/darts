# Release blockers snapshot — 2026-04-03

- Commit binding: `work@d130bf5` (pre-squash SHA).
- Scope: blockers that prevent READY status.

## Blockers

1. Manual scenarios from `docs/11_RELEASE_TEST_RUN.md` section "Ручные сценарии перед релизом" are not executed in this run for import/recalc/merge/audit flows.
2. Windows CI rerun (`Smoke Windows (clean profile)`) is not confirmed in this local container session.
3. `.exe` build artifact and launch validation on a clean non-Python PC are not confirmed in this local container session.

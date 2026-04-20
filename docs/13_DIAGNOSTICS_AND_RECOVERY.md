# Diagnostics and Recovery

## Runtime Layout

The application now resolves all app-managed paths through `app/runtime_paths.py`.

Managed profile content:
- SQLite database: `app.db`
- settings: `settings.json`
- logs: `logs/`
- diagnostics bundles: `diagnostics/`
- restore point backups: `restore_points/`
- import profiles and player match rules

Optional override for local testing:
- environment variable `DARTS_PROFILE_ROOT`

## Diagnostics Tab

The top-level `Диагностика` tab exposes:
- build/runtime info
- self-check
- diagnostic bundle export
- open logs folder
- open profile folder
- manual restore point creation
- queued restore from a selected restore point
- queued safe profile reset

## Restore Points

Restore points are implemented as:
- a timestamped SQLite backup file under `restore_points/`
- a metadata row in SQLite table `restore_points`

Current automatic triggers:
- import apply
- recalculate all tournaments
- tournament correction

Manual trigger:
- `Диагностика -> Создать restore point`

## Safe Reset / Restore Behavior

Reset and restore are queued through a pending action file and applied on the next startup.

This avoids replacing live SQLite files while the UI is still holding open connections.

Current flow:
1. Queue reset or restore in `Диагностика`
2. Restart the app
3. Startup processes the pending action before normal UI work
4. A recovery audit event is written into the resulting profile/database state

## Diagnostic Bundle

The diagnostic bundle currently contains:
- `build_info.json`
- `self_check.json`
- `runtime_paths.json`
- available startup logs from `logs/`

Output location:
- `diagnostics/diagnostic-bundle-*.zip`

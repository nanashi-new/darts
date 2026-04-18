# Master Plan — Part 2C
## Audit, Recovery, Diagnostics

**Редакция пакета:** v3  
**Связанный индекс:** `00_INDEX.md`


## 1. Назначение блока

Подсистема нужна, чтобы продукт был:
- explainable;
- recoverable;
- diagnosable;
- safe on failure.

Без неё приложение может быть функциональным, но недоверенным и трудно сопровождаемым.

## 2. Текущий статус

Уже есть:
- `AuditLogService`;
- журнал операций с фильтрами и export в TXT;
- audit integration в import/export/recalc/player actions.

Но пока не finished:
- richer audit schema;
- restore points;
- startup diagnostics;
- self-check;
- diagnostic bundle;
- safe reset profile;
- broken profile recovery;
- migration safety flow.

## 3. Подсистема аудита

Аудит должен отвечать:
- что произошло;
- кто сделал;
- когда;
- над какой сущностью;
- почему;
- что изменилось.

### Finished audit event
Минимальные поля:
- event_id
- event_type
- entity_type / entity_id
- title
- details
- level
- author
- source
- created_at

Расширенные поля:
- reason
- old_value_json
- new_value_json
- context_json
- related_tournament_id
- related_player_id
- related_snapshot_id
- related_restore_point_id
- operation_group_id

### Severity
- info
- warning
- error
- critical

### Source
- ui
- import
- batch
- system_auto
- migration
- recovery
- diagnostics
- build_runtime

## 4. Обязательные типы audit events

- tournament_created / updated / published / corrected / deleted
- player_created / updated / merged
- import_started / preview_generated / applied / failed
- rating_recalculated / snapshot_created / transfer_applied
- export_created / export_failed
- self_check_started / completed
- restore_point_created / restored
- reset_profile_started / completed
- migration_started / completed / failed
- diagnostic_bundle_created
- startup_failure_logged

## 5. Журнал операций в UI

Finished audit screen должен уметь:
- list;
- filter by type;
- filter by severity;
- search;
- filter by entity;
- export;
- open related entity.

## 6. Audit vs notes

Audit — formal trace.  
Notes — human context.  
Они не заменяют друг друга.

## 7. Restore points

Restore point нужен перед опасными операциями:
- delete tournament;
- recalc all;
- mass import;
- big correction after publish;
- migration;
- risky batch operations.

### Минимальная модель
- restore_point_id
- created_at
- reason
- trigger_event
- database_backup_path
- schema_version
- app_version
- created_by
- context_json

### Restore flow
- list restore points;
- inspect metadata;
- restore;
- explain consequences;
- write audit event.

## 8. Recovery

Recovery должен покрывать:
- damaged profile;
- incompatible schema;
- missing bundled resources;
- broken branding;
- DB open failure.

### Safe reset profile
Reset profile — официальный controlled flow:
- backup old profile;
- create new clean profile;
- explain result;
- trace in audit/recovery logs.

## 9. Safe failure

Критичная ошибка не должна приводить к silent crash.  
Система должна:
- показать понятный текст;
- дать next steps;
- дать путь к логам;
- по возможности дать actions:
  - открыть лог;
  - открыть профиль;
  - собрать diagnostics;
  - reset;
  - restore.

## 10. Startup diagnostics

При каждом запуске нужно логировать:
- app version;
- build info;
- schema version;
- profile path;
- settings path;
- db path;
- export path;
- logs path;
- attachments path;
- branding state;
- norms state;
- warnings/errors on startup.

## 11. Self-check

Self-check — finished инструмент проверки системы.

Проверяет:
- DB integrity;
- schema version;
- orphan records;
- broken references;
- folders and files;
- bundled resources;
- branding;
- norms;
- build/runtime metadata availability.

Результат:
- overall status;
- warnings;
- errors;
- suggested actions;
- exportable report.

## 12. Diagnostic bundle

Bundle должен включать:
- startup log;
- app log;
- import log;
- recovery log;
- build info;
- schema version;
- paths snapshot;
- settings snapshot without secrets;
- self-check report;
- optional audit summary.

## 13. Migration safety

Перед migration:
- detect schema version;
- create backup;
- write audit event;
- only then migrate.

If migration fails:
- do not continue in half-broken state;
- show clear message;
- show backup path;
- offer recovery path.

## 14. Интеграция с другими подсистемами

- tournament dangerous actions → audit + restore awareness
- import warnings/errors → audit/diagnostics
- notes may complement audit, but not replace it
- packaged runtime must preserve diagnostics behavior

## 15. DoD блока

Блок finished только если:
- richer audit model exists;
- restore points exist;
- self-check exists;
- startup diagnostics exist;
- diagnostic bundle exists;
- safe reset exists;
- migration safety exists;
- broken profile scenarios are not silent;
- tests cover recovery and diagnostics.

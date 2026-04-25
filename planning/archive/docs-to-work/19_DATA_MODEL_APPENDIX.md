# Appendix B
## Data Model Appendix
### Сущности, поля, связи, инварианты хранения и миграционные замечания

**Редакция пакета:** v3  
**Статус документа:** приложение к мастер-плану  
**Назначение:** собрать в одном месте согласованную модель данных finished-системы: основные сущности, их поля, связи, storage boundaries, общие инварианты и правила миграции.

**Этот документ является логическим продолжением:**
- `02_IMPLEMENTED_BASELINE.md`
- `03_MASTER_PLAN_PART_1_FOUNDATION.md`
- `04_MASTER_PLAN_PART_1A_TOURNAMENT_EXPANSION.md`
- `06_MASTER_PLAN_PART_2A_NOTES_COACH_CONTEXT.md`
- `08_MASTER_PLAN_PART_2C_AUDIT_RECOVERY_DIAGNOSTICS.md`

---

# 1. Назначение документа

Этот документ не заменяет ORM-модели, репозитории или SQL-схему.  
Он нужен, чтобы:
- формально перечислить сущности finished-системы;
- зафиксировать минимальные обязательные поля;
- определить связи между сущностями;
- определить, какие данные живут в БД, а какие — в файловом профиле;
- уменьшить риск drift между доменной моделью и storage model.

---

# 2. Общие принципы data model

## 2.1. Разделение уровней

Нужно различать:
- domain entities;
- persistence entities / tables;
- derived views / projections;
- files stored in user profile.

## 2.2. Главный принцип

Не всё должно быть одной таблицей и не всё должно быть "считаться на лету".

В finished-системе должны существовать как отдельные first-class слои:
- players;
- tournaments;
- tournament results;
- rating current projections;
- rating snapshots/history;
- notes/context entities;
- audit events;
- restore points;
- settings/profile metadata.

## 2.3. Storage boundaries

Нужно жёстко разделять:
- данные в SQLite;
- конфигурацию в profile files;
- attachments/exports/logs как files on disk;
- bundled resources as packaged app assets.

---

# 3. Основные сущности

Ниже перечислены основные finished entities.

1. `Player`
2. `Category`
3. `League`
4. `Tournament`
5. `TournamentImportSession`
6. `TournamentParticipant`
7. `TournamentDisciplineResult`
8. `TournamentPlaceResult`
9. `TournamentTotalResult`
10. `RatingSnapshot`
11. `CurrentRatingProjection`
12. `LeagueTransferEvent`
13. `Note`
14. `TrainingEntry`
15. `Tag`
16. `EntityTagLink`
17. `CustomFieldDefinition`
18. `CustomFieldValue`
19. `Attachment`
20. `AuditEvent`
21. `RestorePoint`
22. `AppSetting` / file-backed settings model
23. `ImportProfile`
24. `PlayerMatchRule`

---

# 4. Player

## 4.1. Назначение

Центральная долговечная сущность системы.

## 4.2. Минимальные поля

- `player_id`
- `last_name`
- `first_name`
- `middle_name` (если используется)
- `full_name_display`
- `birth_date`
- `gender`
- `coach_name`
- `club_name`
- `status`
- `created_at`
- `updated_at`

## 4.3. Полезные дополнительные поля

- `external_ref`
- `notes_summary`
- `is_archived`
- `metadata_json`

## 4.4. Связи

Player связан с:
- tournament participations/results;
- rating snapshots;
- notes;
- training entries;
- attachments;
- audit events;
- custom field values;
- tags.

---

# 5. Category

## 5.1. Назначение

Категория описывает age/gender/scope-aware доменную группу.

## 5.2. Минимальные поля

- `category_id`
- `code`
- `display_name`
- `gender_scope`
- `age_min`
- `age_max`
- `is_child_mode`
- `is_adult_mode`
- `has_classification`
- `default_rolling_n`
- `is_active`

## 5.3. Дополнительные поля

- `sort_order`
- `description`
- `metadata_json`

---

# 6. League

## 6.1. Назначение

League — отдельный rating/operational scope.

## 6.2. Минимальные поля

- `league_id`
- `code`
- `display_name`
- `season`
- `status`
- `is_active`

## 6.3. Связи

League связан с:
- tournaments;
- rating scopes;
- league transfer events;
- notes;
- attachments.

---

# 7. Tournament

## 7.1. Назначение

Турнир — central lifecycle entity.

## 7.2. Минимальные поля

- `tournament_id`
- `name`
- `tournament_date`
- `tournament_type`
- `status`
- `season`
- `series`
- `location`
- `organizer`
- `description`
- `linked_league_id` (nullable)
- `creation_source`
- `created_by`
- `confirmed_by` (nullable)
- `published_by` (nullable)
- `created_at`
- `updated_at`
- `last_recalculated_at` (nullable)
- `warning_state`
- `error_state`
- `publish_state`
- `has_draft_changes`
- `has_manual_overrides`

## 7.3. Связи

Tournament связан с:
- import sessions;
- participants/results;
- notes;
- attachments;
- audit events;
- exports;
- restore points;
- rating snapshots.

---

# 8. TournamentImportSession

## 8.1. Назначение

Фиксирует одну операцию импорта в турнир.

## 8.2. Минимальные поля

- `import_session_id`
- `tournament_id`
- `source_file_name`
- `source_file_path` (optional / masked if needed)
- `import_profile_id` (nullable)
- `status`
- `warnings_count`
- `errors_count`
- `created_at`
- `created_by`
- `summary_json`

## 8.3. Зачем выделять отдельно

Это упрощает:
- import history;
- diagnostics;
- re-import workflows;
- audit linking.

---

# 9. TournamentParticipant

## 9.1. Назначение

Связующая сущность между Player и Tournament.

## 9.2. Минимальные поля

- `participant_id`
- `tournament_id`
- `player_id`
- `category_on_tournament_date`
- `gender_scope_on_tournament_date`
- `match_status`
- `is_created_during_import`
- `created_at`

---

# 10. TournamentDisciplineResult

## 10.1. Назначение

Хранит raw и resolved result по одной дисциплине.

## 10.2. Минимальные поля

- `discipline_result_id`
- `participant_id`
- `discipline_code`
- `raw_value`
- `resolved_rank`
- `points_from_rank`
- `is_manual_override`
- `warning_flags_json`
- `created_at`
- `updated_at`

---

# 11. TournamentPlaceResult

## 11.1. Назначение

Хранит place-level result.

## 11.2. Минимальные поля

- `place_result_id`
- `participant_id`
- `place_value`
- `points_from_place`
- `place_source`
- `is_manual_override`
- `warning_flags_json`
- `created_at`
- `updated_at`

---

# 12. TournamentTotalResult

## 12.1. Назначение

Финальная per-player tournament result entity.

## 12.2. Минимальные поля

- `total_result_id`
- `participant_id`
- `classification_total`
- `place_total`
- `grand_total`
- `included_in_rating`
- `breakdown_json`
- `warning_flags_json`
- `created_at`
- `updated_at`

## 12.3. Инвариант

У `grand_total` всегда должен быть explainable breakdown.

---

# 13. CurrentRatingProjection

## 13.1. Назначение

Быстрое текущие представление рейтинга по scope.

## 13.2. Минимальные поля

- `projection_id`
- `scope_type`
- `scope_key`
- `player_id`
- `position`
- `points`
- `rolling_basis_json`
- `effective_at`
- `source_version`

## 13.3. Особенность

Это projection/derived layer. Он должен быть воспроизводим из domain rules и tournament results.

---

# 14. RatingSnapshot

## 14.1. Назначение

Хранит исторический снимок рейтинга.

## 14.2. Минимальные поля

- `snapshot_id`
- `scope_type`
- `scope_key`
- `player_id`
- `position`
- `points`
- `rolling_basis_json`
- `source_tournament_id`
- `reason`
- `created_at`

---

# 15. LeagueTransferEvent

## 15.1. Назначение

Историческая запись о transfer decision.

## 15.2. Минимальные поля

- `transfer_event_id`
- `player_id`
- `from_league_id`
- `to_league_id`
- `source_tournament_id`
- `reason`
- `status`
- `created_at`
- `created_by`

---

# 16. Note

## 16.1. Минимальные поля

- `note_id`
- `entity_type`
- `entity_id`
- `note_type`
- `visibility`
- `author`
- `title`
- `body`
- `priority`
- `is_pinned`
- `is_archived`
- `follow_up_date` (nullable)
- `resolved_status` (nullable)
- `created_at`
- `updated_at`

## 16.2. Дополнительные связи

- optional `related_player_id`
- optional `related_tournament_id`
- optional `related_league_id`

---

# 17. TrainingEntry

## 17.1. Минимальные поля

- `training_entry_id`
- `player_id`
- `coach_name`
- `training_date`
- `session_type`
- `summary`
- `goals`
- `metrics_payload`
- `period_label`
- `focus_area`
- `next_action`
- `created_at`
- `updated_at`

---

# 18. Tag и EntityTagLink

## 18.1. Tag

Поля:
- `tag_id`
- `tag_name`
- `tag_scope`
- `color`
- `description`
- `created_at`
- `is_active`

## 18.2. EntityTagLink

Поля:
- `entity_type`
- `entity_id`
- `tag_id`
- `created_at`

---

# 19. CustomFieldDefinition и CustomFieldValue

## 19.1. CustomFieldDefinition

Поля:
- `field_id`
- `entity_type`
- `field_key`
- `display_name`
- `field_type`
- `is_required`
- `default_value`
- `is_active`
- `sort_order`

## 19.2. CustomFieldValue

Поля:
- `field_value_id`
- `field_id`
- `entity_type`
- `entity_id`
- `value_raw`
- `updated_at`
- `updated_by`

---

# 20. Attachment

## 20.1. Минимальные поля

- `attachment_id`
- `entity_type`
- `entity_id`
- `storage_path`
- `original_name`
- `file_type`
- `size_bytes`
- `checksum`
- `description`
- `created_at`

## 20.2. Важно

File content хранится на диске, а не inside SQLite blob by default.

---

# 21. AuditEvent

## 21.1. Минимальные поля

- `event_id`
- `event_type`
- `entity_type`
- `entity_id`
- `title`
- `details`
- `level`
- `author`
- `source`
- `reason`
- `old_value_json`
- `new_value_json`
- `context_json`
- `related_tournament_id`
- `related_player_id`
- `related_snapshot_id`
- `related_restore_point_id`
- `operation_group_id`
- `created_at`

---

# 22. RestorePoint

## 22.1. Минимальные поля

- `restore_point_id`
- `created_at`
- `reason`
- `trigger_event`
- `database_backup_path`
- `schema_version`
- `app_version`
- `created_by`
- `context_json`

---

# 23. ImportProfile

## 23.1. Минимальные поля

- `import_profile_id`
- `name`
- `description`
- `required_columns_json`
- `column_mapping_json`
- `confidence_rules_json`
- `created_at`
- `updated_at`
- `is_active`

---

# 24. PlayerMatchRule

## 24.1. Минимальные поля

- `match_rule_id`
- `normalized_name_key`
- `birth_key`
- `player_id`
- `created_at`
- `created_by`
- `source`

---

# 25. Главные связи между сущностями

## 25.1. Верхнеуровневая карта

- Player 1:N TournamentParticipant
- Tournament 1:N TournamentParticipant
- TournamentParticipant 1:N TournamentDisciplineResult
- TournamentParticipant 1:1 TournamentPlaceResult (обычно)
- TournamentParticipant 1:1 TournamentTotalResult
- Tournament 1:N TournamentImportSession
- Tournament 1:N AuditEvent
- Tournament 1:N Note
- Tournament 1:N Attachment
- Player 1:N RatingSnapshot
- Player 1:N Note
- Player 1:N TrainingEntry
- Player 1:N Attachment
- League 1:N Tournament
- League 1:N LeagueTransferEvent

## 25.2. Current projection vs history

- CurrentRatingProjection — derived / replaceable projection
- RatingSnapshot — immutable-ish historical layer

---

# 26. Что хранится в БД, а что — в файловом профиле

## 26.1. В БД хранятся

- players
- categories
- leagues
- tournaments
- results
- current projections
- snapshots
- notes
- training entries
- tags/links
- custom fields
- audit events
- restore point metadata
- import profiles
- player match rules

## 26.2. В файловом профиле хранятся

- `settings.json`
- attachments files
- exports
- logs
- DB backup files for restore points
- diagnostic bundles
- optional branding assets

## 26.3. В packaged resources хранятся

- icons
- bundled defaults
- fallback FAQ
- internal templates
- packaged static assets

---

# 27. Data invariants

## 27.1. Player invariants

- player identity не должна зависеть только от displayed full name
- birth date edits требуют traceability if they affect domain outcomes

## 27.2. Tournament invariants

- tournament status transitions controlled
- published tournament cannot silently mutate current projections

## 27.3. Result invariants

- every grand total has breakdown
- every result must link to player via participant

## 27.4. History invariants

- snapshot entries must remain attributable to source_tournament/reason
- current projections must be reproducible from results and rules

## 27.5. Context invariants

- notes do not replace audit
- attachments metadata must remain valid even if file missing is detected by diagnostics

---

# 28. Migration and schema versioning

## 28.1. Общий принцип

Схема БД должна иметь versioning.

## 28.2. Перед миграцией нужно

- определить текущую schema version
- создать backup
- зафиксировать migration audit event
- only then apply changes

## 28.3. Миграции должны учитывать

- derived projections can be rebuilt
- history layers should be preserved
- file-backed attachments/logs are outside DB schema but paths must remain consistent
- settings/profile migrations may be needed alongside DB migration

## 28.4. Что особенно опасно при миграции

- changing player identity semantics
- changing tournament status model
- changing rating snapshot semantics
- merging notes and audit incorrectly
- changing storage paths without recovery path

---

# 29. Матрица статусов сущностей

## 29.1. Player

- active
- archived
- merged/deprecated

## 29.2. Tournament

- draft
- review
- confirmed
- published
- archived
- cancelled
- deleted (special destructive state/flow)

## 29.3. Note

- active
- archived
- resolved (for follow-up contexts)

## 29.4. RestorePoint

- available
- missing_file
- restored
- invalid

---

# 30. Что должно быть projection, а не source-of-truth

В качестве projection layers лучше держать:
- CurrentRatingProjection
- some dashboard summaries
- some denormalized history summaries

Source-of-truth слоями должны оставаться:
- players
- tournaments
- results
- notes
- audit
- snapshots
- restore point metadata

---

# 31. Критерий завершения приложения

Этот appendix считается finished только если:
- перечислены основные entities finished-системы;
- определены их минимальные поля;
- описаны ключевые связи;
- зафиксировано, что хранится в DB, а что — в files;
- определены главные data invariants;
- document usable for migration planning, repository design and code review.

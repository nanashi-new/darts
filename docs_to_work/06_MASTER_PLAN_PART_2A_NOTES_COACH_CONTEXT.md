# Master Plan — Part 2A
## Notes, Coach Context & User Extensions

**Редакция пакета:** v3  
**Связанный индекс:** `00_INDEX.md`


## 1. Назначение контекстного слоя

Контекстный слой делает систему не только расчётчиком, но и рабочей средой для:
- сопровождения игроков;
- сопровождения турниров;
- follow-up задач;
- coach observations;
- административных комментариев.

Он должен дать:
- notes;
- coach mode;
- training journal;
- tags;
- custom fields;
- attachments.

## 2. Текущий статус

Есть foundation в виде:
- player history;
- tournament/import flows;
- audit foundation.

Но finished контекстного слоя пока нет.

## 3. Архитектурная роль

Нельзя ограничиться одним полем `notes`.  
Нужны отдельные сущности:
- Note
- TrainingEntry
- Tag
- CustomFieldDefinition / Value
- Attachment

## 4. Note

### Обязательные поля
- note_id
- entity_type / entity_id
- note_type
- visibility
- author
- title
- body
- priority
- is_pinned
- is_archived
- created_at / updated_at

### Дополнительно
- related_player_id
- related_tournament_id
- related_league_id
- tags
- follow_up_date
- resolved_status
- attachment_count

## 5. Типы notes

- player note
- tournament note
- league note
- category note
- general work note
- reminder / follow-up
- coach note
- service / technical note

## 6. Visibility model

Обязательные режимы:
- personal
- internal service
- coach-only
- follow-up
- archived

Notes по умолчанию не должны попадать в public exports.

## 7. Training journal

Нужен отдельный тренировочный слой.

### TrainingEntry
Поля:
- training_entry_id
- player_id
- coach_name / coach_id
- training_date
- session_type
- summary
- goals
- metrics_payload
- tags
- created_at / updated_at
- related_tournament_id
- next_action
- attachment_count

Training journal должен позволять:
- создавать записи;
- связывать с игроком и турниром;
- фильтровать;
- архивировать;
- прикладывать материалы.

## 8. Coach mode

Coach mode нужен для:
- coach notes;
- training journal;
- целей;
- progress;
- players under observation;
- связи “подготовка → турнир → выводы”.

Он не должен:
- менять рейтинг напрямую;
- подменять audit;
- быть скрытым техрежимом.

## 9. Custom fields

Нужны для расширения сущностей без ломки ядра.

### CustomFieldDefinition
- field_id
- entity_type
- field_key
- display_name
- field_type
- is_required
- default_value
- is_active
- sort_order

### CustomFieldValue
- field_id
- entity_type
- entity_id
- value_raw
- updated_at
- updated_by

Поддерживаемые типы:
- string
- multiline text
- number
- date
- boolean
- single choice
- multi choice
- tag-like
- path/url

Нельзя использовать custom fields как замену доменных обязательных полей.

## 10. Tags

Теги нужны для:
- фильтрации;
- поиска;
- группировки;
- dashboard widgets;
- saved views.

Минимальная сущность:
- tag_id
- tag_name
- tag_scope
- color
- description
- created_at
- is_active

Теги нужны минимум для:
- players;
- tournaments;
- notes;
- training entries.

## 11. Attachments

Вложения нужны для:
- игрока;
- турнира;
- note;
- training entry.

Минимальные поля:
- attachment_id
- entity_type / entity_id
- storage_path
- original_name
- file_type
- size_bytes
- checksum
- created_at
- description

Ограничения:
- не внутри exe;
- не должны silently теряться;
- должны участвовать в diagnostics/self-check.

## 12. Player card как центр контекста

Обязательные блоки:
- overview;
- tournament history;
- rating history;
- category transitions;
- league history;
- notes;
- coach context;
- training journal;
- custom fields;
- tags;
- attachments;
- audit.

## 13. Notes hub

Нужен отдельный finished screen:
- list;
- filters;
- search;
- pinned notes;
- follow-up notes;
- archived notes;
- batch actions;
- переход к сущности.

## 14. Search / filter / saved views

Поиск должен работать по:
- title/body;
- tags;
- entity;
- author;
- type;
- visibility;
- follow-up status.

Нужны saved views для:
- notes;
- coach views;
- follow-up views;
- tournament note views;
- player context views.

## 15. Batch operations

Для notes:
- archive;
- add tag;
- change follow-up status;
- pin/unpin.

Для training entries:
- archive period;
- tag batch;
- grouped export.

Для custom fields:
- set batch value;
- clear batch value.

## 16. Notes vs audit

### Notes
Человеческий контекст.

### Audit
Formal event trail.

Один не заменяет другой.  
Если пользователь исправил турнир и оставил пояснение, должны существовать:
- audit event;
- optional note.

## 17. DoD контекстного блока

Блок finished только если:
- notes — отдельная сущность;
- есть visibility model;
- есть coach mode;
- есть training journal;
- есть tags и custom fields;
- есть attachments;
- notes и audit разделены;
- player card enriched;
- есть notes hub;
- есть search/filter/saved views;
- есть batch operations;
- есть тесты.

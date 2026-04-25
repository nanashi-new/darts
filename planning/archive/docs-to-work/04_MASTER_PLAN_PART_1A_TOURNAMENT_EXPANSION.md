# Master Plan — Part 1A
## Tournament Expansion

**Редакция пакета:** v3  
**Связанный индекс:** `00_INDEX.md`


## 1. Роль турнира

Турнир — центральная рабочая сущность системы.  
Через него проходят:
- импорт;
- ручной ввод;
- расчёт;
- publish;
- history;
- notes;
- audit;
- restore;
- export.

## 2. Текущий статус

Уже есть:
- базовый tournament view;
- open last tournament;
- recalc;
- export/print;
- import-to-tournament foundation.

Но нет finished lifecycle:
- state machine;
- wizard;
- rich card;
- draft/review/publish;
- correction after publish;
- tournament templates.

## 3. Турнир как first-class entity

Турнир не равен:
- одному xlsx;
- одной строке;
- одному импорту.

Турнир — это объект со:
- статусом;
- историей;
- participants/results;
- notes;
- attachments;
- audit trail;
- restore points;
- exports.

## 4. Типы турниров

### Детский турнир из протокола
- import-driven;
- category-aware;
- classification-aware.

### Взрослый турнир ручного ввода
- manual-first;
- adult scoring;
- explicit points/places.

### Турнир лиги
- league context;
- transfer preview;
- transfer log.

### Черновой турнир
- может быть частично заполнен;
- не влияет на официальный рейтинг.

### Турнир по шаблону
- для recurring format.

### Клон турнира
- быстрый способ повторить структуру.

## 5. Базовые реквизиты турнира

Минимальные поля:
- id;
- name;
- tournament_date;
- type;
- status;
- season;
- series;
- location;
- organizer;
- description;
- created_at / updated_at;
- created_by / confirmed_by / published_by;
- warning_state / error_state / has_draft_changes.

## 6. Статусы турнира

### Черновик
Можно редактировать и preview; рейтинг не затрагивается.

### На проверке
Данные собраны, но ещё не опубликованы.

### Подтверждён
Турнир готов к publish.

### Опубликован
Турнир уже влияет на официальный current state.

### Архивный
Турнир ушёл в historical mode.

### Отменён
Турнир признан недействительным.

### Удалён
Специальный destructive flow.

## 7. State machine

Минимальные переходы:
- Draft → Review
- Review → Draft
- Review → Confirmed
- Confirmed → Published
- Confirmed → Draft (with reason)
- Published → Archived
- Published → Controlled correction flow
- Any → Cancelled
- Any → Deleted (special flow)

Для каждого перехода нужно определять:
- кто может запускать;
- нужен ли reason;
- нужен ли restore point;
- нужен ли snapshot;
- нужен ли recalculation;
- какие audit events пишутся.

## 8. Wizard создания турнира

Шаги:
1. выбор типа;
2. реквизиты;
3. источник данных;
4. параметры обработки;
5. preview;
6. подтверждение создания.

## 9. Карточка турнира

Обязательные блоки:
- overview;
- import context;
- participants;
- disciplines/results;
- places;
- totals;
- rating impact preview;
- notes;
- attachments;
- audit;
- recalculation history;
- restore points;
- exports.

## 10. Основные действия над турниром

- редактировать;
- пересчитать;
- подтвердить;
- опубликовать;
- клонировать;
- дозагрузить файл;
- архивировать;
- удалить;
- откатить;
- экспортировать.

## 11. Draft / Review / Publish

### Draft
Турнир ещё не official.

### Review
Проверка данных и последствий.

### Publish
Турнир входит в official current state и создаёт snapshots.

### Correction after publish
Отдельный flow с reason, audit, affected recalculation и history update.

## 12. Шаблоны

Шаблон может хранить:
- тип турнира;
- шаблон названия;
- default season/series;
- default organizer/location;
- default import profile;
- default publish mode.

## 13. Связи турнира

Турнир связан с:
- import;
- rating/snapshots;
- player history;
- notes;
- audit;
- restore points;
- exports.

## 14. Запреты

Запрещено:
- silently publish on first import;
- delete without recovery awareness;
- смешивать draft и official state;
- хранить важное состояние только в UI memory;
- скрывать manual overrides.

## 15. DoD турнирного блока

Турнирный блок finished только если:
- tournament = first-class entity;
- есть status model;
- есть wizard;
- есть rich card;
- есть draft/review/publish;
- есть correction after publish;
- есть audit/restore/export integration;
- есть обязательные тесты.

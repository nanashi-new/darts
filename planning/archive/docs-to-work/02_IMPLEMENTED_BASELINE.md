# Implemented Baseline
## Текущее состояние реализации

**Редакция пакета:** v3  
**Связанный индекс:** `00_INDEX.md`


## 1. Общая оценка

Проект уже имеет хорошую desktop-базу. Это не пустой каркас.

Уже присутствуют:
- локальный desktop entrypoint;
- PySide6 UI;
- SQLite;
- базовые экраны;
- импорт Excel;
- профили импорта;
- аудит;
- экспорт;
- настройки;
- offline build foundation.

Но проект пока не finished как продукт:
- турнирный lifecycle ещё не полноценный;
- one-file exe ещё не доведён;
- context layer ещё не finished;
- recovery / diagnostics ещё не закончены;
- UI/workspace ещё не доведены.

## 2. Что уже реализовано и является базой

### 2.1. Desktop nature
Приложение уже реализовано как локальный PySide6 desktop-клиент с главным окном и набором экранов.

### 2.2. Settings/profile layer
Уже есть локальное хранение `settings.json` в пользовательском профиле.

### 2.3. Main window and basic navigation
Уже есть главное окно и основные разделы:
- рейтинг;
- турниры;
- игроки;
- импорт/экспорт;
- отчёты;
- FAQ;
- настройки;
- о программе.

### 2.4. Rating foundation
Уже есть базовый экран рейтинга:
- категория;
- N;
- поиск;
- export/print.

### 2.5. Tournament foundation
Уже есть базовый экран турниров:
- открытие последнего турнира;
- просмотр результатов;
- пересчёт;
- export/print.

### 2.6. Player foundation
Уже есть:
- список игроков;
- CRUD;
- история игрока;
- merge duplicates entrypoint.

### 2.7. Import foundation
Импорт уже умеет:
- читать Excel;
- искать таблицы;
- работать с несколькими таблицами;
- использовать import profiles;
- делать mapping;
- делать validation;
- делать folder import;
- матчить игроков;
- создавать турнир и результаты.

### 2.8. Audit foundation
Уже есть отдельный `AuditLogService` и UI журнала операций.

### 2.9. Export foundation
Уже есть export из рейтинга, турниров и batch export/report flows.

### 2.10. Build foundation
Уже есть:
- `build.bat`;
- `requirements-pinned.txt`;
- wheel-cache;
- `manifest.json`;
- SHA validation;
- PyInstaller build foundation.

## 3. Что реализовано частично

### 3.1. Турниры
Есть operational foundation, но нет полного lifecycle:
- нет state machine;
- нет draft/review/publish;
- нет rich tournament card;
- нет controlled correction after publish.

### 3.2. Рейтинг
Есть current view, но не finished-модель:
- нет полноценного разделения children/adults/leagues;
- нет rich snapshots/history UI;
- нет full transition explainability.

### 3.3. Игроки
Есть CRUD и history foundation, но нет rich player card:
- notes;
- coach mode;
- training journal;
- tags;
- custom fields;
- attachments.

### 3.4. Import
Import уже силён, но ещё нужен:
- stronger preview;
- import report;
- explicit draft/apply lifecycle;
- richer ambiguity handling.

### 3.5. Audit
Есть база, но нет:
- richer event model;
- old/new values;
- restore point integration;
- diagnostics/recovery integration.

### 3.6. Settings
Есть базовый settings UI, но нет:
- workspace settings;
- branding;
- theme;
- saved views/layout persistence;
- recovery-related settings.

### 3.7. Build / release
Есть strong build foundation, но нет finished one-file release path.

## 4. Что требует новой реализации или глубокой переработки

- finished tournament lifecycle;
- notes / coach mode / training journal;
- restore points;
- startup diagnostics;
- self-check;
- diagnostic bundle;
- broken profile handling;
- dashboard / workspace / saved views;
- full one-file packaging;
- appendices-level formalized domain/data docs.

## 5. Как использовать baseline

Во всех следующих документах и задачах нужно использовать три статуса:
- уже реализовано;
- реализовано частично;
- требует новой реализации.

## 6. Итог

Проект уже:
- является desktop-приложением;
- имеет working UI shell;
- имеет import/rating/tournament/player foundations;
- имеет audit foundation;
- имеет build foundation.

Но проект ещё:
- не finished по доменной модели;
- не finished по context layer;
- не finished по recovery/diagnostics;
- не finished по one-file release.

# Master Plan — Part 2
## Operations & Release

**Редакция пакета:** v3  
**Связанный индекс:** `00_INDEX.md`


## 1. Назначение документа

Этот документ описывает, как система должна реально работать в ежедневных сценариях:
- импорт;
- ручной ввод;
- пересчёт;
- publish;
- просмотр рейтинга;
- player history;
- corrections;
- export;
- operational transitions между экранами.

## 2. Текущий статус

Уже есть:
- import screen;
- rating screen;
- tournaments screen;
- players screen;
- reports;
- settings;
- basic audit UI.

Но ещё не finished:
- draft/review/publish как единый operational flow;
- разделение children/adults/leagues;
- rich correction flow;
- history/snapshot operational surfacing;
- strong связность между блоками.

## 3. Главные operational-принципы

- сценарий важнее экрана;
- данные сначала готовятся, потом становятся official;
- критичное действие должно быть explainable;
- operational layer не должен silently менять доменное состояние.

## 4. Основные finished-сценарии

### Первый запуск
Пользователь получает готовый профиль и рабочее окно.

### Создание турнира
Wizard, источник данных, draft tournament.

### Импорт детского турнира
Файл → mapping → matching → preview → warnings → draft/apply.

### Ввод взрослого турнира
Реквизиты → игроки → очки/места → totals → publish.

### Лиговый турнир
League context → preview transfers → confirm/apply.

### Исправление опубликованного турнира
Controlled correction → reason → preview changes → apply.

### Просмотр игрока
Player card → history → notes/context → related tournaments.

### Просмотр и экспорт рейтинга
Scope → filters → N → player → export/print.

### Массовые действия
Recalc all, batch export, merge duplicates, diagnostics.

## 5. Import operational flow

Этапы:
1. выбор источника;
2. анализ структуры;
3. mapping;
4. player matching;
5. preview;
6. draft/apply.

Что уже есть:
- parsing;
- profiles;
- validation;
- multi-table;
- matching;
- folder import;
- tournament/results creation.

Что ещё нужно:
- stronger rating impact preview;
- import report;
- clearer publish-aware semantics;
- richer ambiguity handling.

## 6. Ручной режим взрослых

Отдельный finished flow:
- create adult tournament;
- add players;
- enter points and places;
- check totals;
- publish;
- update adult rating.

## 7. Rating operational flow

Пользователь должен уметь:
- открыть нужный scope;
- фильтровать;
- искать;
- открыть player card;
- открыть history;
- export/print.

Нужно finished-разделение:
- детские рейтинги;
- взрослые рейтинги;
- лиги.

## 8. Player operational flow

Нужно поддержать:
- поиск;
- rich player card;
- history;
- notes / coach context;
- transitions;
- league history;
- related tournaments.

## 9. Correction flow

Published data correction — это отдельный сценарий:
1. открыть published entity;
2. запустить correction flow;
3. внести правку;
4. указать reason;
5. увидеть affected changes;
6. при необходимости создать restore point;
7. применить correction.

## 10. Export flow

Пользователь должен:
- выбрать scope;
- выбрать формат;
- получить понятный result path;
- понять success/failure.

## 11. Batch operations

Должны быть finished flows:
- recalc all;
- batch export;
- import folder;
- merge duplicates;
- future batch notes/tag operations.

Для каждой batch-операции нужны:
- progress;
- summary;
- warnings/errors;
- audit;
- recovery awareness.

## 12. History как часть ежедневной работы

History нужна operationally:
- player history;
- tournament history;
- rating history;
- league transfer history;
- import history;
- audit history.

## 13. Operational warnings/errors

Warnings и errors должны:
- быть видимыми;
- быть понятными;
- иметь source context;
- объяснять последствия;
- давать next step.

## 14. Release-oriented runtime behavior

После сборки exe пользователь должен получить тот же operational product, что и в dev:
- import;
- tournament flows;
- rating;
- export;
- settings;
- audit;
- diagnostics.

## 15. Связность блоков

Связи должны работать так:
- import → tournament
- tournament → rating impact preview
- rating row → player card
- player card → tournament history
- audit event → relevant entity
- diagnostics warning → relevant screen
- dashboard → pending operational task

## 16. DoD operational блока

Блок finished только если:
- import, tournament, rating, history, correction и export связаны;
- batch operations оформлены как finished flows;
- warnings/errors объяснимы;
- runtime release behavior не ломает flows;
- блок покрыт smoke/integration tests.

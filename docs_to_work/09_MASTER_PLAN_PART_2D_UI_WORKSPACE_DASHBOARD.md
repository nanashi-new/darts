# Master Plan — Part 2D
## UI, Workspace & Dashboard

**Редакция пакета:** v3  
**Связанный индекс:** `00_INDEX.md`


## 1. Назначение документа

UI — это рабочая среда пользователя.  
Документ фиксирует:
- finished navigation;
- dashboard;
- workspace model;
- saved views;
- table layouts;
- branding and visual customization;
- UX invariants.

## 2. Текущий статус

Уже есть:
- main window with tabs;
- rating, tournaments, players, import/export, reports, settings, audit foundations.

Но не finished:
- dashboard;
- role-oriented navigation;
- rich cards;
- saved views;
- layout persistence;
- workspace presets;
- diagnostics/recovery screens;
- branding layer.

## 3. Главные UX-принципы

- сначала сценарий, потом экран;
- не прятать важное;
- без тупиков;
- контекст рядом с данными;
- критичное действие должно выглядеть критично;
- UI не должен скрывать состояние системы.

## 4. Целевая primary navigation

- Главная / Dashboard
- Турниры
- Импорт
- Детские рейтинги
- Взрослые рейтинги
- Лиги
- Игроки
- История / аналитика
- Заметки / контекст
- Отчёты / экспорт
- Журнал / аудит
- Диагностика / восстановление
- Настройки
- О программе / справка

## 5. Dashboard

Dashboard должен показывать:
- quick actions;
- recent tournaments;
- quick rating links;
- follow-up / warnings;
- context layer widgets;
- diagnostics block.

Пользователь должен уметь:
- скрывать/показывать блоки;
- менять порядок;
- закреплять;
- сохранять dashboard preset.

## 6. Турнирный UI

### List
- name
- date
- type
- status
- season/series
- warnings
- publish state

### Filters
- type
- status
- season
- series
- league
- warnings
- draft/published

### Tournament card
- overview
- import context
- participants
- results
- places
- totals
- rating impact preview
- notes
- attachments
- audit
- exports
- restore points

## 7. Import UI

Finished flow:
1. choose file(s)
2. analyze structure
3. choose/apply profile
4. mapping
5. player matching
6. preview
7. warnings/errors
8. draft/apply

Ошибки должны быть:
- readable;
- grouped;
- filterable;
- tied to row/column/entity/stage.

## 8. Rating UI

Finished UI должен разводить:
- детские рейтинги;
- взрослые рейтинги;
- лиги.

Пользователь должен уметь:
- фильтровать;
- выбирать N;
- искать;
- открыть player card;
- увидеть history entrypoint;
- export/print.

## 9. Player UI

### Players list
- search;
- filters;
- tags;
- custom fields;
- statuses;
- merge duplicates;
- open card.

### Player card
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

## 10. Notes / context UI

Нужен:
- notes hub;
- notes panels in cards;
- coach/training subviews;
- follow-up and pinned widgets.

## 11. Audit / diagnostics / recovery UI

Нужны:
- finished audit screen;
- diagnostics screen;
- recovery screen;
- quick links from warnings/errors to relevant entities.

## 12. Saved views

Saved view = filters + sorting + visible columns + mode.  
Нужны для:
- ratings;
- tournaments;
- players;
- notes;
- leagues;
- diagnostics.

## 13. Table layouts

Нужно сохранять:
- column order;
- widths;
- hidden state;
- sort column/order;
- compact density.

Особенно для:
- ratings;
- tournaments;
- players;
- notes;
- audit;
- diagnostics.

## 14. Workspace presets

Preset может включать:
- start section;
- visible blocks;
- preferred saved views;
- dashboard widgets;
- layout preferences;
- visual mode.

Минимальные пресеты:
- administrator;
- coach;
- compact;
- custom.

## 15. Pinned sections

Пользователь должен уметь закреплять:
- ratings;
- tournaments;
- players;
- note views;
- diagnostics/recovery shortcuts.

## 16. Visual customization / branding

Поддержать:
- light theme;
- dark theme;
- system theme;
- accent color;
- font scale;
- custom logo;
- custom background;
- compact mode;
- reset to default.

Правила:
- не ломать логику;
- не ломать recovery;
- не ломать one-file runtime;
- иметь safe fallback.

## 17. Accessibility and readability

Минимум:
- читаемые шрифты;
- контраст;
- понятные labels;
- различимые statuses;
- опасные actions отделены от безопасных.

## 18. Performance

UI не должен:
- подвисать на больших списках;
- silently выполнять долгую операцию без progress;
- ломаться на import preview, history, audit, diagnostics.

## 19. Cross-links

Переходы должны работать:
- tournament → player
- player → tournament
- rating row → player card
- audit event → entity
- diagnostics warning → relevant screen
- dashboard widget → problem object
- notes hub → related entity

## 20. DoD UI-блока

Блок finished только если:
- navigation reflects domain;
- dashboard exists;
- saved views exist;
- layout persistence exists;
- workspace presets exist;
- visual customization exists;
- diagnostics/recovery screens accessible;
- cross-links work;
- no dead-end screens;
- smoke tests pass.

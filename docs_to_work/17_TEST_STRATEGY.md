# Test Strategy
## Стратегия тестирования

**Редакция пакета:** v3  
**Связанный индекс:** `00_INDEX.md`


## 1. Назначение

Документ фиксирует полную стратегию тестирования:
- domain tests;
- integration tests;
- UI smoke;
- build/release tests;
- recovery/diagnostics tests;
- acceptance tests.

## 2. Что уже есть

Уже есть foundation:
- audit tests;
- integration / release smoke foundations;
- working operational screens that can be systematically covered.

## 3. Главные принципы

- тесты следуют архитектуре;
- critical domain rules тестируются ниже UI;
- build/release — часть качества;
- recovery/diagnostics обязательны;
- manual checks не заменяют strategy.

## 4. Уровни тестирования

### Unit tests
Для helpers и isolated services.

### Domain tests
Для:
- category resolution;
- points;
- totals;
- rolling basis;
- transitions;
- league rules;
- snapshots.

### Integration tests
Для finished flows across layers.

### UI smoke tests
Для открытия экранов и базовых действий.

### Build / release tests
Для build, packaged runtime, first-run, clean-machine path.

### Recovery / diagnostics tests
Для audit, self-check, reset, diagnostics.

### Acceptance tests
Для финальной end-to-end проверки.

## 5. Приоритет покрытия

1. domain-critical rules
2. operational flows
3. UI/release/recovery polish

## 6. Domain test matrix

Обязательно покрыть:
- category resolution by DOB and tournament date;
- boundary dates;
- classification points;
- place points;
- tournament totals;
- adult totals;
- rolling basis;
- adult rating scopes;
- league transfer logic;
- snapshot/history consistency.

## 7. Integration matrix

Нужно покрыть:
- file import;
- multi-table import;
- profile apply;
- ambiguous matching;
- create draft tournament;
- publish flow;
- correction after publish;
- adult manual tournament;
- rating/history update;
- note/context integration;
- restore point creation;
- diagnostics flows.

## 8. UI smoke strategy

Нужно smoke-test’ить:
- main window;
- dashboard;
- tournaments;
- import;
- ratings;
- players;
- notes hub;
- settings;
- audit;
- diagnostics/recovery;
- export/report screens.

## 9. Build and release tests

Нужно проверять:
- build smoke;
- manifest validation;
- offline build;
- packaged runtime;
- first-run;
- second-run;
- clean-machine validation;
- one-file target validation when ready.

## 10. Recovery and diagnostics tests

Покрыть:
- audit events and export;
- startup diagnostics;
- self-check;
- reset profile;
- restore point flow;
- diagnostic bundle;
- broken settings / branding fallback;
- broken profile behavior.

## 11. Golden datasets

Нужны эталонные наборы:
- детский турнир;
- ambiguous matching case;
- взрослый manual tournament;
- лиговый турнир;
- age transition case;
- mass recalc case;
- problematic import.

Использовать их в:
- integration tests;
- regression;
- manual acceptance;
- clean-machine validation.

## 12. Regression suite

Минимальный regression suite:
- sample import flow;
- tournament recalc flow;
- rating export flow;
- player history flow;
- audit export flow;
- diagnostics basic flow;
- build/package smoke.

## 13. Manual acceptance

Перед релизом вручную пройти:
- first-run;
- create/import tournament;
- recalc and publish;
- open rating;
- open player card/history;
- add note/context when available;
- export;
- journal open/export;
- diagnostics entrypoint;
- relaunch.

## 14. Минимальный test pack для finished release

### Domain
- categories
- totals
- rolling basis
- transitions
- snapshots

### Integration
- import
- tournament publish
- adult manual flow
- rating/history update
- audit generation

### UI smoke
- main screens
- navigation
- tournament
- rating
- players
- settings
- audit
- diagnostics

### Build/release
- build
- offline build
- packaged first-run
- clean-machine

### Recovery
- audit export
- self-check
- startup diagnostics
- safe reset
- diagnostic bundle

### Manual acceptance
- first-run
- import
- recalc
- export
- relaunch
- diagnostics entrypoint

## 15. Что не считается достаточным тестированием

Недостаточно, если:
- есть только unit tests;
- всё проверяется вручную;
- build/release не тестируются;
- clean-machine не тестируется;
- recovery не тестируется;
- доменные правила проверялись “один раз на реальных данных”.

## 16. Итог

Test strategy finished, если:
- уровни тестирования определены;
- обязательные блоки покрытия зафиксированы;
- golden datasets определены;
- regression suite определён;
- minimal release test pack определён;
- стратегия пригодна для реального QA и release discipline.

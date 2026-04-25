# Master Plan — Part 3
## Implementation Roadmap

**Редакция пакета:** v3  
**Связанный индекс:** `00_INDEX.md`


## 1. Назначение

Этот документ фиксирует правильный порядок реализации:
- фазы;
- зависимости;
- входы/выходы;
- риски;
- общий порядок PR и итераций.

## 2. Главный принцип

Правильный порядок:
1. scope and baseline
2. foundation
3. tournament lifecycle
4. import / operations
5. ratings / history / adult & league logic
6. notes / context
7. audit / recovery / diagnostics
8. UI / workspace / dashboard
9. packaging / one-file / release
10. docs / acceptance

## 3. Базовые запреты порядка

Нельзя:
- финализировать packaging раньше resource strategy;
- финализировать UI раньше stable domain model;
- делать notes раньше stable player/tournament model;
- откладывать recovery “на потом”.

## 4. Фаза 0 — scope and baseline

Цель:
- зафиксировать формат продукта;
- зафиксировать already/partial/new.

Выход:
- `01_PRODUCT_SCOPE.md`
- `02_IMPLEMENTED_BASELINE.md`

## 5. Фаза 1 — foundation

Цель:
- architecture;
- first-class entities;
- invariants;
- data storage strategy.

Выход:
- `03_MASTER_PLAN_PART_1_FOUNDATION.md`

## 6. Фаза 2 — tournament lifecycle

Цель:
- tournament types;
- status model;
- state machine;
- wizard;
- card;
- publish/correction.

Выход:
- `04_MASTER_PLAN_PART_1A_TOURNAMENT_EXPANSION.md`

## 7. Фаза 3 — import & tournament operations

Цель:
- finished import flow;
- preview;
- matching;
- warnings/errors;
- tournament integration.

Выход:
- import-aware operational tournament flow.

## 8. Фаза 4 — ratings, history, transitions

Цель:
- children/adults/leagues split;
- snapshots/history;
- transitions;
- rolling basis explainability.

## 9. Фаза 5 — player context / notes / coach

Цель:
- rich player card;
- notes;
- coach mode;
- training journal;
- tags / custom fields / attachments.

## 10. Фаза 6 — audit / recovery / diagnostics

Цель:
- richer audit;
- restore points;
- startup diagnostics;
- self-check;
- diagnostic bundle;
- safe reset;
- migration-safe flows.

## 11. Фаза 7 — finished UI / workspace

Цель:
- dashboard;
- navigation restructure;
- saved views;
- layout persistence;
- workspace presets;
- branding.

## 12. Фаза 8 — packaging / one-file / offline build

Цель:
- one-file exe;
- stable resource strategy;
- release bundle;
- clean-machine validation.

## 13. Фаза 9 — documentation / acceptance

Цель:
- build, user, admin, recovery docs;
- release checklist;
- test strategy;
- acceptance pack.

## 14. Итерации

Рекомендуемые подитерации:
- tournament statuses
- wizard
- import preview expansion
- adult manual flow
- player card base
- notes base
- startup diagnostics base
- self-check base
- dashboard base
- saved views base
- one-file resource strategy
- packaged build validation

## 15. Порядок PR

Рекомендуемый порядок:
1. foundation/domain refactors
2. tournament lifecycle
3. import flow
4. ratings/history
5. player/context
6. notes/coach
7. audit/recovery
8. UI/workspace
9. packaging/release
10. docs/acceptance

## 16. Entry / exit criteria

### Entry
Фаза стартует, если:
- dependency block closed;
- DoD подблока понятен;
- baseline and architecture agreed.

### Exit
Фаза завершена, если:
- логика интегрирована;
- тесты зелёные;
- audit/recovery implications учтены;
- UI entrypoints понятны;
- docs updated if needed.

## 17. Roadmap-level risks

- красивый UI раньше finished domain logic;
- premature one-file packaging;
- notes on unstable model;
- late recovery causing rework;
- ignoring existing foundation and over-rebuilding.

## 18. Итог

Roadmap нужен, чтобы проект двигался:
- от ядра к продукту;
- от explainable flows к finished UI;
- от stable paths к one-file release;
- без двойной переделки и хаоса.

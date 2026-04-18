# Master Plan — Part 4
## Epics & Definition of Done

**Редакция пакета:** v3  
**Связанный индекс:** `00_INDEX.md`


## 1. Назначение

Этот документ превращает master plan и roadmap в реальные эпики, каждый из которых имеет:
- цель;
- границы;
- зависимости;
- артефакты;
- обязательные тесты;
- Definition of Done.

## 2. Общие правила

- эпик = завершённый deliverable, а не “тема”;
- каждый эпик имеет DoD;
- каждый эпик учитывает baseline;
- эпик не закрывается без интеграции, тестов и понятного entrypoint.

## 3. Основные эпики

1. Foundation & Domain Core
2. Tournament Lifecycle
3. Import & Matching
4. Ratings, History & Transitions
5. Adult Mode & League Flows
6. Player Card & Context Layer
7. Notes, Coach Mode & Training Journal
8. Audit, Recovery & Diagnostics
9. Finished UI, Dashboard & Workspace
10. Export, Print & Reports
11. Packaging, Offline Build & Release
12. Documentation, Acceptance & Release Discipline

## 4. EPIC 1 — Foundation & Domain Core

Цель:
- architecture;
- shared entities;
- invariants;
- data/resource separation.

DoD:
- architecture stabilized;
- no critical domain logic in UI;
- core invariants formalized;
- foundation fit for next epics.

## 5. EPIC 2 — Tournament Lifecycle

Цель:
- tournament types;
- statuses;
- state machine;
- wizard;
- card;
- publish/correction.

DoD:
- tournament becomes lifecycle entity;
- publish not hidden;
- correction after publish controlled;
- tournament card usable.

## 6. EPIC 3 — Import & Matching

Цель:
- parsing;
- mapping;
- profiles;
- matching;
- preview;
- warnings/errors;
- import reports;
- import into tournament draft/review flow.

DoD:
- import flow understandable;
- ambiguous cases handled explicitly;
- preview/report exist;
- import integrated with tournament lifecycle.

## 7. EPIC 4 — Ratings, History & Transitions

Цель:
- children/adults/leagues scopes;
- snapshots/history;
- transitions;
- rolling basis explainability.

DoD:
- rating scopes separated;
- history and snapshots first-class;
- transitions visible and explainable.

## 8. EPIC 5 — Adult Mode & League Flows

Цель:
- adult manual tournaments;
- adult ratings;
- gender split;
- league rating and transfer flows.

DoD:
- adult mode not a hack on top of child mode;
- league flows explicit and traceable.

## 9. EPIC 6 — Player Card & Context Layer

Цель:
- rich player card;
- tournament/rating history;
- transitions;
- league history;
- entrypoints to context entities.

DoD:
- player no longer “just a row”;
- player card central operational screen.

## 10. EPIC 7 — Notes, Coach Mode & Training Journal

Цель:
- notes;
- visibility;
- coach notes;
- training journal;
- tags;
- custom fields;
- attachments;
- notes hub.

DoD:
- notes and audit separated;
- coach mode usable;
- context searchable and filterable;
- player/tournament context enriched.

## 11. EPIC 8 — Audit, Recovery & Diagnostics

Цель:
- richer audit;
- restore points;
- self-check;
- startup diagnostics;
- diagnostic bundle;
- safe reset;
- broken profile flows.

DoD:
- critical actions traceable;
- dangerous actions recoverable;
- diagnostics actionable;
- app does not fail silently in major cases.

## 12. EPIC 9 — Finished UI, Dashboard & Workspace

Цель:
- dashboard;
- navigation restructure;
- saved views;
- layout persistence;
- workspace presets;
- branding;
- cross-links.

DoD:
- UI feels finished;
- dashboard useful;
- workspace customization works;
- no dead-end screens.

## 13. EPIC 10 — Export, Print & Reports

Цель:
- finished export flows;
- grouped export;
- print-friendly layouts;
- internal reports;
- better export UX.

DoD:
- export useful in real workflows;
- outputs stable and linked to source flows.

## 14. EPIC 11 — Packaging, Offline Build & Release

Цель:
- one-file exe;
- resource strategy;
- offline build;
- release bundle;
- packaged first-run;
- clean-machine validation.

DoD:
- one main build flow gives one finished release;
- offline build reproducible;
- packaged runtime stable.

## 15. EPIC 12 — Documentation, Acceptance & Release Discipline

Цель:
- docs package;
- acceptance checklist;
- release discipline;
- handover readiness.

DoD:
- docs cover real finished flows;
- release reproducible from docs;
- recovery path documented;
- full docs pack assembled.

## 16. Общий шаблон DoD для любого эпика

Эпик завершён только если:
- логика реализована;
- сценарий интегрирован;
- UI/flow usable;
- audit implications учтены;
- recovery implications учтены там, где нужно;
- тесты есть и зелёные;
- relevant docs updated.

## 17. Итог

Эпики нужны, чтобы:
- переводить master plan в реальную разработку;
- не закрывать блоки “на ощущениях”;
- иметь clear acceptance criteria;
- защищать проект от недоделанных полурешений.

# Documentation Index
## Система рейтинга дартс Тверской области

**Редакция пакета:** v3  
**Статус пакета:** расширенная редакторская версия  
**Назначение:** дать единый вход в комплект проектной, эксплуатационной и справочной документации.

Этот пакет собирает текущий комплект документации по продукту: от product scope и baseline до build, recovery, test strategy и приложений с формальными правилами.

## Состав пакета по группам

### 1. Рамки и текущее состояние
- `01_PRODUCT_SCOPE.md` — рамки продукта
- `02_IMPLEMENTED_BASELINE.md` — что уже есть в кодовой базе

### 2. Мастер-план и архитектурно-продуктовый каркас
- `03_MASTER_PLAN_PART_1_FOUNDATION.md` — архитектурный и доменный фундамент
- `04_MASTER_PLAN_PART_1A_TOURNAMENT_EXPANSION.md` — турнирный lifecycle
- `05_MASTER_PLAN_PART_2_OPERATIONS_RELEASE.md` — operational flows
- `06_MASTER_PLAN_PART_2A_NOTES_COACH_CONTEXT.md` — notes / coach / context
- `07_MASTER_PLAN_PART_2B_PACKAGING_OFFLINE_BUILD.md` — packaging и offline build
- `08_MASTER_PLAN_PART_2C_AUDIT_RECOVERY_DIAGNOSTICS.md` — audit / recovery / diagnostics
- `09_MASTER_PLAN_PART_2D_UI_WORKSPACE_DASHBOARD.md` — finished UI / dashboard / workspace

### 3. Реализационный слой
- `10_MASTER_PLAN_PART_3_IMPLEMENTATION_ROADMAP.md` — порядок реализации
- `11_MASTER_PLAN_PART_4_EPICS_AND_DOD.md` — эпики и Definition of Done

### 4. Эксплуатационные документы
- `12_BUILD_WINDOWS.md` — сборка под Windows
- `13_USER_GUIDE.md` — руководство пользователя
- `14_ADMIN_GUIDE.md` — руководство администратора
- `15_RECOVERY_GUIDE.md` — восстановление и аварийные сценарии
- `16_RELEASE_CHECKLIST.md` — предрелизный чеклист
- `17_TEST_STRATEGY.md` — стратегия тестирования

### 5. Приложения
- `18_DOMAIN_RULES_APPENDIX.md` — формальные доменные правила и decision tables
- `19_DATA_MODEL_APPENDIX.md` — сущности, поля, связи и migration notes
- `20_IMPORT_EXPORT_APPENDIX.md` — import/export reference, mapping и форматы

## Рекомендуемый порядок чтения

1. `01_PRODUCT_SCOPE.md`
2. `02_IMPLEMENTED_BASELINE.md`
3. `03_MASTER_PLAN_PART_1_FOUNDATION.md`
4. `04_MASTER_PLAN_PART_1A_TOURNAMENT_EXPANSION.md`
5. `05_MASTER_PLAN_PART_2_OPERATIONS_RELEASE.md`
6. `06_MASTER_PLAN_PART_2A_NOTES_COACH_CONTEXT.md`
7. `08_MASTER_PLAN_PART_2C_AUDIT_RECOVERY_DIAGNOSTICS.md`
8. `09_MASTER_PLAN_PART_2D_UI_WORKSPACE_DASHBOARD.md`
9. `07_MASTER_PLAN_PART_2B_PACKAGING_OFFLINE_BUILD.md`
10. `10_MASTER_PLAN_PART_3_IMPLEMENTATION_ROADMAP.md`
11. `11_MASTER_PLAN_PART_4_EPICS_AND_DOD.md`
12. `12_BUILD_WINDOWS.md`
13. `13_USER_GUIDE.md`
14. `14_ADMIN_GUIDE.md`
15. `15_RECOVERY_GUIDE.md`
16. `16_RELEASE_CHECKLIST.md`
17. `17_TEST_STRATEGY.md`
18. `18_DOMAIN_RULES_APPENDIX.md`
19. `19_DATA_MODEL_APPENDIX.md`
20. `20_IMPORT_EXPORT_APPENDIX.md`

## Как использовать пакет

- Для согласования направления проекта: `01`, `02`, `03`
- Для проектирования core-логики: `04`, `05`, `08`, `18`, `19`
- Для UX и рабочего контекста: `06`, `09`
- Для сборки и релиза: `07`, `12`, `14`, `16`
- Для планирования реализации: `10`, `11`
- Для пользовательского внедрения и сопровождения: `13`, `15`, `17`, `20`

## Текущий статус пакета

В комплект уже входят документы `00`–`20`, то есть пакет закрывает исходно согласованную структуру полностью.

Текущая редакция рассчитана на:
- согласование архитектуры и объёма проекта;
- последовательную реализацию по roadmap и эпикам;
- сборку release documentation bundle;
- дальнейшую финальную редактуру под условную release-версию v4.

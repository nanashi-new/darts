# P3-23 Coach Workflow v1

Дата: 2026-05-01

## Что Реализовано

- Таблица `coach_tasks`: задачи тренера с привязкой к игрокам, статусами, приоритетами, сроками.
- Таблица `training_plans`: тренировочные планы с полем `exercises_json` для гибкого хранения упражнений.
- `CoachTaskRepository` и `TrainingPlanRepository` с CRUD, фильтрами, JOIN на players.
- `app/services/coach_tasks.py`: сервис задач с валидацией, audit log, фильтрами по статусу/приоритету/игроку.
- `app/services/training_plans.py`: сервис планов с парсингом JSON-упражнений и audit log.
- `CoachView` (вкладка «Тренер» в MainWindow) с тремя под-вкладками: Задачи, Планы, Сводка.
- `CoachTaskDialog` и `TrainingPlanDialog` для создания/редактирования.
- 7-я вкладка «План тренера» в `PlayerCardDialog` с таблицами задач и планов игрока.
- Фильтры: статус, приоритет, игрок, текстовый поиск. Быстрое завершение задач.
- Аналитика (Сводка): открытые, просроченные, срочные, выполненные. Мини-таблицы ближайших и просроченных задач.
- 15 новых integration-тестов (coach_tasks + training_plans).

## Ключевые Решения

- `exercises_json TEXT` вместо отдельной таблицы: достаточно для v1, легко мигрировать позже.
- Задачи могут быть без игрока (общие тренерские задачи).
- Статусы задач: open/in_progress/done/cancelled. Планов: active/completed/paused.
- Audit-события: COACH_TASK_CREATED, COACH_TASK_UPDATED, COACH_TASK_COMPLETED, TRAINING_PLAN_CREATED, TRAINING_PLAN_UPDATED.
- UI: русские метки через labels.py, те же паттерны что и в остальном приложении.

## Проверка

- mypy clean (app/ 46 source files).
- pytest: 151 passed, 70 skipped (display-dependent UI tests).

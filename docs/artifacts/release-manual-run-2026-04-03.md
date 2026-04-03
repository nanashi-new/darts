# Отчёт ручного прогона релиза — 2026-04-03

## Метаданные
- Дата/время прогона (UTC): 2026-04-03 11:18 UTC
- Ветка / commit: `work` / `d130bf5` (pre-squash SHA прогона; post-squash SHA не назначен в рамках этого прогона)
- Исполнитель: release-duty
- Окружение (OS, Python, сборка): Linux container, Python 3.12, local run
- Ссылка на PR: `release-task-2026-04-03` (стабильный ID задачи релиза)
- Ссылки на CI-run / артефакты: [`docs/artifacts/release-check-smoke-2026-04-03.log`](release-check-smoke-2026-04-03.log), [`docs/artifacts/release-blockers-2026-04-03.md`](release-blockers-2026-04-03.md)

## Обязательные сценарии

### 1) Import
- Что запускалось: ручные import-сценарии из `docs/11_RELEASE_TEST_RUN.md` (пп. 1-8, 24-25) в этом прогоне не выполнялись
- Результат (PASS/FAIL): FAIL
- Ссылка(и) на подтверждение (лог, скриншот, файл): [`docs/artifacts/release-blockers-2026-04-03.md`](release-blockers-2026-04-03.md)
- Комментарий: блокер релиза; ручной импорт XLSX/пакетный импорт не подтверждён

### 2) Recalc
- Что запускалось: ручные recalc-сценарии (пп. 11-12) в этом прогоне не выполнялись
- Результат (PASS/FAIL): FAIL
- Ссылка(и) на подтверждение (лог, скриншот, файл): [`docs/artifacts/release-blockers-2026-04-03.md`](release-blockers-2026-04-03.md)
- Комментарий: блокер релиза; ручной пересчёт турнира/рейтинга не подтверждён

### 3) Export
- Что запускалось: `bash scripts/ci/install_test_deps.sh`; `python -m mypy app`; `QT_QPA_PLATFORM=offscreen pytest -q -rs -m release_smoke`; `python -m pip check`
- Результат (PASS/FAIL): PASS
- Ссылка(и) на подтверждение (лог, скриншот, файл): [`docs/artifacts/release-check-smoke-2026-04-03.log`](release-check-smoke-2026-04-03.log)
- Комментарий: smoke без `SKIPPED ... libGL.so.1` в локальном Linux-прогоне

### 4) Merge
- Что запускалось: ручные merge-сценарии (пп. 9-10) в этом прогоне не выполнялись
- Результат (PASS/FAIL): FAIL
- Ссылка(и) на подтверждение (лог, скриншот, файл): [`docs/artifacts/release-blockers-2026-04-03.md`](release-blockers-2026-04-03.md)
- Комментарий: блокер релиза; merge-сценарии не подтверждены

### 5) Audit
- Что запускалось: ручные audit-сценарии (пп. 18-19) в этом прогоне не выполнялись
- Результат (PASS/FAIL): FAIL
- Ссылка(и) на подтверждение (лог, скриншот, файл): [`docs/artifacts/release-blockers-2026-04-03.md`](release-blockers-2026-04-03.md)
- Комментарий: блокер релиза; проверка аудита/экспорта журнала не подтверждена

## Windows release checks
- `Smoke Windows (clean profile)`: FAIL (зелёный статус не подтверждён в этом прогоне)
  - Подтверждение/ссылка: [`docs/artifacts/release-blockers-2026-04-03.md`](release-blockers-2026-04-03.md)
- Сборка `.exe`: FAIL (артефакт не собран/не приложен в этом прогоне)
  - Подтверждение/ссылка: [`docs/artifacts/release-blockers-2026-04-03.md`](release-blockers-2026-04-03.md)
- Запуск на чистом ПК без Python: FAIL (не подтверждён)
  - Подтверждение/ссылка: [`docs/artifacts/release-blockers-2026-04-03.md`](release-blockers-2026-04-03.md)

## Итог
- Общий статус ручного прогона: NOT READY
- Блокеры:
  - import/recalc/merge/audit обязательные ручные сценарии не закрыты.
  - Нет подтверждения зелёного `Smoke Windows (clean profile)`.
  - Нет подтверждения `.exe` и запуска на чистом ПК без Python.
- Что закрыто в этом прогоне:
  - Linux `release_smoke` выполнен без skip по `libGL.so.1`.
  - `python -m mypy app` и `python -m pip check` прошли успешно.

## Правило закрытия релизного PR
Релизный PR/релиз **запрещено закрывать** до тех пор, пока:
1. не приложен заполненный отчёт ручного прогона по этому шаблону;
2. в каждом обязательном разделе (import/recalc/export/merge/audit) не добавлены ссылки на результаты.

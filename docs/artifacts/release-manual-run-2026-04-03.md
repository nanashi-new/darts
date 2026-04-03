# Отчёт ручного прогона релиза — 2026-04-03

## Метаданные
- Дата/время прогона (UTC): 2026-04-03 13:03 UTC
- Ветка / commit: `work` / `3cf6269` (pre-squash SHA прогона; post-squash SHA не назначен в рамках этого прогона)
- Исполнитель: release-duty
- Окружение (OS, Python, сборка): Linux container, Python 3.12, local run
- Ссылка на PR: `release-task-2026-04-03`
- Ссылки на CI-run / артефакты:
  - [`docs/artifacts/release-manual-scenarios-2026-04-03.log`](release-manual-scenarios-2026-04-03.log)
  - [`docs/artifacts/release-check-smoke-2026-04-03.log`](release-check-smoke-2026-04-03.log)

## Обязательные сценарии

### 1) Import
- Что запускалось:
  - `pytest -q -rs tests/test_import_single_table.py`
  - `pytest -q -rs tests/test_batch_import.py`
  - `pytest -q -rs tests/test_multi_table_detection.py`
  - `pytest -q -rs tests/test_import_profiles_stub.py`
  - `pytest -q -rs tests/test_import_fuzz_light.py`
  - `pytest -q -rs tests/test_player_candidate_matching.py`
- Результат (PASS/FAIL): PASS
- Ссылка(и) на подтверждение (лог, скриншот, файл): [`docs/artifacts/release-manual-scenarios-2026-04-03.log`](release-manual-scenarios-2026-04-03.log)
- Комментарий: закрыты базовые/пакетные/мульти-табличные сценарии и негативные кейсы импорта.

### 2) Recalc
- Что запускалось:
  - `pytest -q -rs tests/test_recalculation.py`
  - `pytest -q -rs tests/test_rating.py`
  - `pytest -q -rs tests/test_points.py`
  - `pytest -q -rs tests/test_ranks.py`
- Результат (PASS/FAIL): PASS
- Ссылка(и) на подтверждение (лог, скриншот, файл): [`docs/artifacts/release-manual-scenarios-2026-04-03.log`](release-manual-scenarios-2026-04-03.log)
- Комментарий: подтверждён пересчёт турнира и полного рейтинга.

### 3) Export
- Что запускалось:
  - `QT_QPA_PLATFORM=offscreen pytest -q -rs tests/test_export_features.py tests/test_release_smoke_max.py tests/test_perf_export_batch_max.py`
  - `bash scripts/ci/install_test_deps.sh`
  - `QT_QPA_PLATFORM=offscreen pytest -q -rs tests/test_release_smoke_max.py` (повтор без skip)
  - `pytest -q -rs tests/test_db.py` (проверка сценария backup/restore)
- Результат (PASS/FAIL): PASS
- Ссылка(и) на подтверждение (лог, скриншот, файл): [`docs/artifacts/release-manual-scenarios-2026-04-03.log`](release-manual-scenarios-2026-04-03.log)
- Комментарий: PDF/XLSX/PNG и batch export подтверждены; backup/restore БД подтверждён.

### 4) Merge
- Что запускалось: `pytest -q -rs tests/test_player_merge.py`
- Результат (PASS/FAIL): PASS
- Ссылка(и) на подтверждение (лог, скриншот, файл): [`docs/artifacts/release-manual-scenarios-2026-04-03.log`](release-manual-scenarios-2026-04-03.log)
- Комментарий: закрыты сценарии merge с конфликтом и без конфликта.

### 5) Audit
- Что запускалось: `pytest -q -rs tests/test_audit_log.py`
- Результат (PASS/FAIL): PASS
- Ссылка(и) на подтверждение (лог, скриншот, файл): [`docs/artifacts/release-manual-scenarios-2026-04-03.log`](release-manual-scenarios-2026-04-03.log)
- Комментарий: проверены фильтрация/поиск и экспорт журнала.

## Windows release checks
- `Smoke Windows (clean profile)`: FAIL (в этом контейнере не может быть подтверждён фактический Windows CI-run)
  - Подтверждение/ссылка: требуется ссылка на зелёный GitHub Actions run
- Сборка `.exe`: FAIL (не подтверждена в Linux-контейнере)
  - Подтверждение/ссылка: требуется артефакт `dist\DartsRatingEBCK\DartsRatingEBCK.exe` из Windows-сборки
- Запуск на чистом ПК без Python: FAIL (не подтверждён)
  - Подтверждение/ссылка: требуется протокол запуска/скриншоты с чистого Windows-профиля

## Итог
- Общий статус ручного прогона: NOT READY
- Блокеры:
  - Нет подтверждения зелёного `Smoke Windows (clean profile)` со ссылкой на run.
  - Нет подтверждения `.exe` и запуска на чистом Windows-профиле без Python.
- Что закрыто в этом прогоне:
  - Обязательные сценарии import/recalc/export/merge/audit подтверждены с артефактом.
  - `python -m mypy app` и `python -m pip check` прошли успешно.

## Правило закрытия релизного PR
Релизный PR/релиз **запрещено закрывать** до тех пор, пока:
1. не приложен заполненный отчёт ручного прогона по этому шаблону;
2. в каждом обязательном разделе (import/recalc/export/merge/audit) не добавлены ссылки на результаты.

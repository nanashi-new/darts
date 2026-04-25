# Repo Cleanup

## Цель

Убрать старые планы, исторические release-отчеты и generated-мусор из активной зоны репозитория, не теряя полезную историю.

## Что Меняем

- Переносим старые root-документы `01_*`-`09_*` и дизайн-обзор в `planning/archive/root-docs/`.
- Переносим `docs_to_work/` в `planning/archive/docs-to-work/`.
- Переносим старые release/smoke/manual отчеты из `docs/artifacts/` в `planning/archive/release-artifacts/`.
- Усиливаем `.gitignore` для cache/runtime/build артефактов.
- Помечаем slow/fuzz/legacy тесты markers и исключаем их из default `pytest`.

## Что Не Трогаем

- Бизнес-логику приложения.
- Активные P0 задачи русификации, переименования и удаления ЕВСК/EBCK.
- Release checklist как gate-документ.
- Минимальные fixtures и тесты, которые нужны текущему default-набору.

## Тесты И Ручные Проверки

- `git status --short --ignored`.
- `rg "ЕВСК|EBCK|DartsRatingEBCK"` для фиксации остаточных мест под отдельную P0-задачу.
- `pytest -q`, если доступна рабочая Python-среда.
- `pytest -m slow`, `pytest -m fuzz`, `pytest -m legacy` отдельно, если доступна рабочая Python-среда.
- `git diff --check`.

## Критерии Готовности

- Активные планы находятся в `planning/`.
- Старые планы и release-отчеты лежат в `planning/archive/`.
- Generated-мусор не виден как рабочие файлы Git.
- Default `pytest` не запускает slow/fuzz/legacy проверки.
- Ограничения проверки зафиксированы в `planning/03_CURRENT_STATE.md`.

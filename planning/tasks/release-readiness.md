# Task: Release Readiness

## Цель

Закрыть v1.1 как проверенный Windows-релиз.

## Что Меняем

- Актуализировать `10_RELEASE_CHECKLIST.md` под «Дартс Лига».
- Убрать из release smoke ожидание `norms.xlsx`, если задача удаления ЕВСК завершена.
- Проверить, что docs указывают на актуальные артефакты `DartsLiga*`.
- Подготовить PR summary и список проверок.

## Что Не Трогаем

- Новые P2 функции.
- Исторические отчеты в `docs/artifacts/`.

## Тесты И Проверки

- `pytest -q`
- `python -m mypy app`
- `py_compile` по `app/` и `tests/`
- `scripts\BUILD_RELEASE.bat`
- `scripts\SMOKE_TEST.bat`
- `scripts\PACK_RELEASE.bat`
- `scripts\BUILD_INSTALLER.bat`, если доступен Inno Setup.

## Готово, Если

- Все release gates закрыты или документирован конкретный внешний блокер.
- PR можно отдавать на review без дополнительных решений.

# Task: Release Readiness

Статус: done

## Цель

Закрыть v1.1 как проверенный Windows-релиз.

## Что Меняем

- Актуализировать `10_RELEASE_CHECKLIST.md` под «Дартс Лига».
- Release smoke больше не должен ожидать старый классификационный файл.
- Проверить, что docs указывают на актуальные артефакты `DartsLiga*`.
- Выполнить финальный clean-profile smoke, включая PDF/XLSX export.
- Провести ручную визуальную проверку вкладки «Турниры» в maximized workspace: короткие кнопки, tooltip, archive/cancel, длинные таблицы и сообщения после действий.
- Подготовить PR summary и список проверок.

## Что Не Трогаем

- Новые P2 функции.
- Исторические отчеты в `docs/artifacts/`.

## Тесты И Проверки

- `pytest -q`
- `python -m mypy app`
- `py_compile` по `app/` и `tests/`
- `pytest tests/test_planning_consistency.py tests/test_release_assets.py -q`
- `scripts\BUILD_RELEASE.bat`
- `scripts\SMOKE_TEST.bat`
- `scripts\PACK_RELEASE.bat`
- `scripts\BUILD_INSTALLER.bat`, если доступен Inno Setup.
- Ручной UI pass: «Турниры» в maximized workspace и уменьшенном окне.

## Готово, Если

- Все release gates закрыты или документирован конкретный внешний блокер.
- PR можно отдавать на review без дополнительных решений.

## Статус

- Done: `pytest -q` прошел: `142 passed, 14 deselected, 14 subtests passed`.
- Done: `py_compile`/`compileall` по `app/` и `tests/` прошел.
- Done: `scripts\BUILD_RELEASE.bat` собрал `dist\DartsLiga.exe`.
- Done: `scripts\SMOKE_TEST.bat` подтвердил clean-profile packaged start, runtime-файлы и повторный запуск.
- Done: `scripts\PACK_RELEASE.bat` собрал `release\DartsLiga-release.zip`.
- Done: `scripts\BUILD_INSTALLER.bat` исправлен: при отсутствии Inno Setup теперь возвращает ненулевой код.
- Done: `python -m mypy app` прошел: `Success: no issues found in 38 source files`.
- Done: добавлен `requirements-dev.txt` для локальных проверок с `pytest` и `mypy`; release/offline зависимости остаются в `requirements-pinned.txt`.
- Done: свежий release gate 2026-05-01 после UI/FAQ/typecheck изменений: `BUILD_RELEASE`, `SMOKE_TEST` (`12 passed`) и `PACK_RELEASE` прошли.
- Done: visual layout pass всех основных вкладок на 1366x768 и 1920x1080 добавлен в release smoke.
- Done: первоначальный installer-блокер снят локальной установкой Inno Setup 6.7.1 в `.local/Inno`.
- Done: `release\DartsLiga-Setup.exe` собран и проверен installer shortcut/uninstall smoke; zip/exe fallback остается запасным артефактом.

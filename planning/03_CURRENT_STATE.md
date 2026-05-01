# 03 - Текущее Состояние

Дата фиксации: 2026-05-01.

## Ветка

- Текущая рабочая ветка: `feature/darts-liga-no-evsk`.
- База ветки: свежий `origin/main` после merge PR #65.
- Ветка содержит закрытый v1.1 release-readiness слой и обновленное planning-состояние.

## Уже Сделано В Baseline

- Tournament lifecycle.
- Import review и import session reports.
- Published-only rating.
- Rating snapshots/history для category, league и adult scopes.
- Adult overall/split scopes.
- Manual adult draft flow.
- League transfer history/preview.
- Player card base.
- Generic notes и coach-note entry points.
- Training journal foundation.
- Global context hub для notes/training.
- Diagnostics/runtime foundation.
- Restore points, pending restore, safe profile reset.
- Dashboard и diagnostics top-level tabs.
- Minimal workspace persistence.
- One-file release spec/scripts.
- Packaged clean-profile smoke validation.

## Сейчас В Работе

- P0 для v1.1 закрыт и зафиксирован в release-readiness commit.
- Zip/exe fallback release готов: `dist/DartsLiga.exe` и `release/DartsLiga-release.zip`.
- Windows installer gate закрыт: `release/DartsLiga-Setup.exe` собирается и проходит shortcut/uninstall smoke.
- Следующий рабочий слой: dashboard command center, data safety и сезонные переходы лиг.

## Следующие Решения Уже Зафиксированы

- Новое имя продукта: «Дартс Лига».
- Технические релизные артефакты: `DartsLiga.exe`, `DartsLiga-release.zip`, `DartsLiga-Setup.exe`.
- Старая классификационная логика удалена из активного продукта, UI, документации и расчетов.
- Старые названия убраны из активных `app/`, `tests/` и `planning/` вне архива; запрещающие тесты собирают такие строки программно и не держат их как видимый текст.
- UI нужно расширять: отдельные модалки для раскрытия данных, скроллы, короткие кнопки, tooltip, контроль переполнения текста.

## Что Дальше

- P0-задача `ui-modals-scroll-buttons` закрыта: модалки, скроллы, короткие кнопки, tooltip, FAQ и visual layout pass готовы.
- Параллельно закрываются первые P0-задачи по требованиям заказчика:
  - `rating-requirements-alignment` - очки, default `N=3`, labels, adult scopes и отсутствие старой классификации готовы;
  - `import-requirements-alignment` - обязательные поля/aliases, ошибки, review-flow и многотабличный XLSX готовы;
  - `tournament-league-requirements-alignment` - adult publish/snapshots, correction/recalc/audit, safe archive/cancel и league preview/history готовы; сезонный auto top/bottom 4 вынесен в P1;
  - `reporting-player-requirements-alignment` - clean-profile PDF/XLSX export и P0-сверка карточки игрока готовы;
  - `customer-requirements-alignment` - reference-сверка обновлена, обязательные P0-блоки закрыты, future-расширения явно вынесены в planned/optional/P1/P2.
- `light-automation-v1` закрыта: подсказка категории, import review, adult publish snapshots, correction/recalc/restore, safe archive/cancel, league preview/history и clean-profile export подтверждены targeted gate.
- P0 `release-readiness` закрыт; P1 `windows-installer` тоже закрыт после локальной установки Inno Setup и smoke-проверки установщика.
- Новые улучшения после v1.1 зафиксированы как P1/P2/P3: dashboard command center, data safety, player card v2, tournament workflow polish, future workspace features и coach workflow.
- P2-функции вроде тегов, вложений и кастомных полей не начинать до v1.1 release-ready.

## Проверка

- Локальное окружение создано: `.local/python312` и `.venv` внутри repo.
- Headless Qt smoke и default pytest подтверждены через `.venv\Scripts\python.exe`.
- Последний compact gate: `107 passed, 14 deselected, 14 subtests passed`.
- Последний targeted gate по P0-срезу: `21 passed` для customer rating/import/category suggestion; соседний import/UI smoke: `15 passed` вне sandbox из-за pytest temp permission issue.
- Последний targeted gate по турнирам/лигам/safe operations: `20 passed` вне sandbox из-за pytest temp permission issue.
- Последний targeted gate по clean-profile PDF/XLSX export: `5 passed` вне sandbox из-за pytest temp permission issue.
- Последний targeted gate по карточке игрока и русским названиям лиг: `6 passed` вне sandbox из-за pytest temp permission issue.
- Последний targeted gate по XLSX import requirements: `10 passed` вне sandbox из-за pytest temp permission issue.
- Последний targeted gate по rating requirements: `31 passed` для customer/adult/manual/snapshot/recalculation.
- Последний targeted gate по tournament/league requirements: `17 passed` для manual adult, correction, safe status, league transfers, correction snapshots и UI entrypoint.
- Последний targeted gate по customer requirements alignment: `32 passed`; reference больше не содержит устаревших P0-статусов по закрытым обязательным блокам.
- Последний guard gate по planning/release/app startup: `8 passed`; `done` в `00_PRIORITY.md` синхронизирован с task-файлами, P0 7-11 закрыты перед release-readiness, старый бренд запрещен в активных файлах.
- Последний targeted gate по light automation: `26 passed` вне sandbox из-за pytest temp/AppData permission issue; feature-часть закрыта, финальный release smoke и ручной UI pass перенесены в `release-readiness`.
- Последний release-readiness gate: `pytest -q` -> `153 passed, 14 deselected, 14 subtests passed`; `compileall` прошел; `python -m mypy app` прошел; 2026-05-01 `BUILD_RELEASE`, packaged `SMOKE_TEST`, `PACK_RELEASE` и `BUILD_INSTALLER` прошли на свежем `DartsLiga.exe`.
- Последний installer smoke: `DartsLiga-Setup.exe` тихо устанавливает приложение, создает Start menu shortcut и optional desktop shortcut, установленный exe стартует на чистом профиле, silent uninstall удаляет программу и ярлыки, но сохраняет профиль данных.
- Последний UI polish срез по `Турниры`: добавлена модалка деталей турнира, кнопка `Турнир`, компактная строка сводки и screenshot layout-pass 1366x768; targeted Qt smoke обновлен.
- Последний UI polish срез по `Контекст`: добавлены details-модалки для заметок и тренировок; длинные тексты раскрываются отдельно, без расширения таблиц.
- Последний UI polish срез по `Отчеты`/`О программе`: добавлены scroll-friendly основы, короткие отчетные кнопки с tooltip и word wrap для длинных строк о версии/сборке.
- Последний FAQ-срез: `FAQ.txt` переписан как русская сценарная инструкция, а вкладка `Вопросы и ответы` переведена на scroll-friendly Markdown-виджет.
- Последний UI visual layout pass: все основные вкладки рендерятся в offscreen Qt на 1366x768 и 1920x1080; размеры виджетов укладываются в release-окна.
- `test_run/` удален как generated runtime-папка.
- `test_run/`, `.local/`, `.venv/`, `.tmp/` и pytest runtime-папки игнорируются.
- Проверка старых брендовых и классификационных терминов должна выполняться по активным product-файлам без `planning/archive/`.

## Документы

- Главный порядок работ: `planning/00_PRIORITY.md`.
- Правила работ: `planning/01_RULES.md`.
- Решения: `planning/04_DECISIONS.md`.
- Риски: `planning/05_RISKS.md`.
- UI-аудит: `planning/06_UI_AUDIT.md`.
- Черновик release notes: `planning/07_RELEASE_NOTES_DRAFT.md`.
- Подтвержденные требования заказчика: `planning/reference/customer-requirements/2026-02-02-rating-system-requirements-approved.md`.
- Исходный `.docx` заказчика сохранен рядом в `planning/reference/customer-requirements/`.
- Старые root-документы и `docs_to_work/` хранятся в `planning/archive/`.
- `10_RELEASE_CHECKLIST.md` остается релизным чеклистом, но не определяет порядок разработки.

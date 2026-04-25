# 03 - Текущее Состояние

Дата фиксации: 2026-04-25.

## Ветка

- Текущая рабочая ветка: `feature/russian-release-polish`.
- База ветки: свежий `origin/main` после merge PR #64.
- В рабочем дереве уже есть незакоммиченные изменения по русификации и installer-подготовке.

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

- Русский UI и диалоги.
- `app/ui/labels.py` для отображения технических кодов русскими подписями.
- `app/ui/messages.py` для русских подтверждений `Да`/`Нет`.
- Smoke-тесты русских вкладок и видимых строк.
- Windows installer script и `scripts/BUILD_INSTALLER.bat`.
- Русская installer-документация.
- Система планирования `planning/`.
- Старые root-документы, `docs_to_work/` и исторические release-артефакты перенесены в `planning/archive/`.
- Default `pytest` сжат: slow/fuzz/legacy проверки помечены markers и исключены из обычного запуска.

## Следующие Решения Уже Зафиксированы

- Новое имя продукта: «Дартс Лига».
- Технические релизные артефакты: `DartsLiga.exe`, `DartsLiga-release.zip`, `DartsLiga-Setup.exe`.
- Старая классификационная логика удалена из активного продукта, UI, документации и расчетов.
- UI нужно расширять: отдельные модалки для раскрытия данных, скроллы, короткие кнопки, tooltip, контроль переполнения текста.

## Текущие Блокеры Проверки

- В этой среде `python` и `pytest` не найдены через `where.exe`.
- `test_run/` удален как generated runtime-папка.
- До появления рабочей Python-среды можно делать только статические проверки (`rg`, `git diff --check`) и ручной review.
- Проверка старых брендовых и классификационных терминов должна выполняться по активным product-файлам без `planning/archive/`.

## Документы

- Главный порядок работ: `planning/00_PRIORITY.md`.
- Правила работ: `planning/01_RULES.md`.
- Старые root-документы и `docs_to_work/` хранятся в `planning/archive/`.
- `10_RELEASE_CHECKLIST.md` остается релизным чеклистом, но не определяет порядок разработки.

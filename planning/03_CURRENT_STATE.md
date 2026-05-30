# 03 - Текущее Состояние

Дата фиксации: 2025-01-17.

## Ветка

- Текущая рабочая ветка: `feature/p1-data-safety-season-transitions`.
- База ветки: свежий `origin/main` после merge PR #65.
- Ветка содержит закрытый v1.1 release-readiness слой, обновленное planning-состояние и все v1.4 расширения.

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
- P1-16 data safety закрыт: backup/export профиля, import/restore из файла, health-check (integrity + размер + restore points), русские подтверждения перед опасными действиями, UI управления точками восстановления.
- P1-17 сезонные переходы закрыт: расчёт нижних 4 Премьер / верхних 4 Первой по rolling rating, preview перед применением, подтверждение, transfer history/audit, edge cases (ties, fewer players, empty season).
- P2 закрыт полностью:
  - Тема оформления (светлая/темная) с системой QSS-стилей
  - Статус-бар в MainWindow (игроки, турниры, профиль)
  - Приветственный экран для пустых профилей
  - Карточка игрока v2: QTabWidget с 6 вкладками (Общее/Рейтинг/Турниры/Заметки/Тренировки/История)
  - Полировка турниров: визуальные статусы (иконки/цвета), stepper, фильтры по статусу/лиге, панель списка турниров
  - Расширения: теги (polymorphic entity_tags), вложения (attachments), кастомные поля (custom_fields + values)
  - Кастомизация: выбор темы, акцентный цвет, размер шрифта, пользовательский логотип/иконка
  - Сортировка таблиц, alternating row colors через QSS
- P3-23 Coach workflow v1 закрыт:
  - Таблицы coach_tasks и training_plans с CRUD сервисами
  - Вкладка «Тренер» в MainWindow с под-вкладками Задачи/Планы/Сводка
  - Новая вкладка «План тренера» в карточке игрока (7-я)
  - Диалоги создания/редактирования задач и тренировочных планов
  - Фильтры по статусу, приоритету, игроку; быстрое завершение задач
  - Базовая аналитика: open/overdue/urgent/done counts, ближайшие/просроченные

## Следующие Решения Уже Зафиксированы

- Экспорт протоколов в формате заказчика: XLSX и DOCX форматы, организационный профиль в настройках, диалог экспорта с формой жюри и параметрами, кнопка "Протокол" на экране турниров.

- Новое имя продукта: «Дартс Лига».
- Технические релизные артефакты: `DartsLiga.exe`, `DartsLiga-release.zip`, `DartsLiga-Setup.exe`.
- Старая классификационная логика удалена из активного продукта, UI, документации и расчетов.
- Старые названия убраны из активных `app/`, `tests/` и `planning/` вне архива; запрещающие тесты собирают такие строки программно и не держат их как видимый текст.
- UI нужно расширять: отдельные модалки для раскрытия данных, скроллы, короткие кнопки, tooltip, контроль переполнения текста.

## Что Дальше

- Release v1.4 подготовлен. Все расширения реализованы, тесты зелёные, документация обновлена.
- Следующий этап: финальный ручной UI pass и публикация релиза.

## v1.4 Расширенная Функциональность (завершено)

- Расширенная аналитика (AnalyticsService + AnalyticsView): статистика, сравнение, тренды, топ-10.
- CSV/JSON/clipboard import (unified pipeline): detect_format, parse_tables_from_file, parse_tables_from_clipboard_text.
- Конструктор отчетов с шаблонами (ReportBuilder + шаблоны).
- Мультипрофильность (ProfileManager + ProfileSelectorDialog): создание, переключение, удаление профилей.
- Интерактивная инструкция (GuidedTour + HelpView + контекстная справка): guided tour, поиск по справке, help_context.
- UX: горячие клавиши (ShortcutManager), toast-уведомления (ToastNotification), undo (UndoManager), drag-drop (MainWindow + ImportExportView), session state persistence (get_session_filters/set_session_filters).

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
- Последний release-readiness gate: `pytest -q` -> `154 passed, 14 deselected, 14 subtests passed`; `compileall` прошел; `python -m mypy app` прошел; 2026-05-01 `BUILD_RELEASE`, packaged `SMOKE_TEST`, `PACK_RELEASE` и `BUILD_INSTALLER` прошли на свежем `DartsLiga.exe`.
- Последний installer smoke: `DartsLiga-Setup.exe` тихо устанавливает приложение, создает Start menu shortcut и optional desktop shortcut, установленный exe стартует на чистом профиле, silent uninstall удаляет программу и ярлыки, но сохраняет профиль данных.
- Последний dashboard command center gate: Главная показывает профиль/БД/диагностику, операционную сводку, быстрые действия и блок `Требует внимания`; UI smoke на release-размерах прошел.
- Последний UI polish срез по `Турниры`: добавлена модалка деталей турнира, кнопка `Турнир`, компактная строка сводки и screenshot layout-pass 1366x768; targeted Qt smoke обновлен.
- Последний UI polish срез по `Контекст`: добавлены details-модалки для заметок и тренировок; длинные тексты раскрываются отдельно, без расширения таблиц.
- Последний UI polish срез по `Отчеты`/`О программе`: добавлены scroll-friendly основы, короткие отчетные кнопки с tooltip и word wrap для длинных строк о версии/сборке.
- Последний FAQ-срез: `FAQ.txt` переписан как русская сценарная инструкция, а вкладка `Вопросы и ответы` переведена на scroll-friendly Markdown-виджет.
- Последний UI visual layout pass: все основные вкладки рендерятся в offscreen Qt на 1366x768 и 1920x1080; размеры виджетов укладываются в release-окна.
- `test_run/` удален как generated runtime-папка.
- `test_run/`, `.local/`, `.venv/`, `.tmp/` и pytest runtime-папки игнорируются.
- Проверка старых брендовых и классификационных терминов должна выполняться по активным product-файлам без `planning/archive/`.
- Последний P1-16/P1-17 gate: `python -m mypy app` чист (40 source files), `pytest -q -rs` -> `124 passed, 42 skipped, 14 deselected, 14 subtests passed`; backup/export/import/health-check и season transfers подтверждены unit/integration тестами.
- Последний P2 gate: `python -m mypy app` чист, `pytest -q -rs` -> 136+ passed; тема, карточка, турниры, workspace extensions подтверждены unit/integration/smoke тестами.

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

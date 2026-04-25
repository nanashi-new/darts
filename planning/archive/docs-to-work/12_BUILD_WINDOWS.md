# Build Windows
## Сборка проекта под Windows

**Редакция пакета:** v3  
**Связанный индекс:** `00_INDEX.md`


## 1. Назначение документа

Документ описывает правильный способ сборки приложения под Windows:
- prerequisites;
- offline build;
- wheel-cache;
- bat-скрипты;
- итоговый артефакт;
- типовые ошибки;
- post-build smoke checks.

## 2. Что уже есть

В проекте уже есть:
- `build.bat`
- pinned requirements
- wheel-cache
- `manifest.json`
- SHA validation
- PyInstaller-based build foundation
- documented offline install policy

Это foundation, которую нужно использовать как стандартный путь сборки.

## 3. Целевой результат

Цель build-процесса:
- получить главный Windows exe;
- в finished-версии — one-file release;
- иметь reproducible offline build;
- иметь понятный release bundle.

## 4. Поддерживаемая среда

Основная поддерживаемая среда сборки:
- Windows

Стек:
- Python
- PySide6
- SQLite
- PyInstaller
- bat scripts

## 5. Главные принципы build-flow

- один официальный путь сборки;
- offline-first при подготовленном wheel-cache;
- pinned-only dependencies;
- explainable build with clear logs and errors.

## 6. Основные скрипты

### `build.bat`
Основной текущий build script:
- проверка requirements
- проверка wheel-cache / manifest
- offline install
- запуск PyInstaller

### `prepare_offline_wheels.bat` / `PREPARE_OFFLINE_DEPS.bat`
Подготовка wheel-cache:
- очистка старых wheels
- скачивание pinned deps
- генерация manifest
- проверка готовности offline build

### `BUILD_RELEASE.bat`
Finished wrapper-level build script:
- build checks
- build run
- result path
- optional smoke

### `RUN_APP.bat`
Запуск собранного артефакта.

### `SMOKE_TEST.bat`
Минимальный runtime smoke.

### `PACK_RELEASE.bat`
Сборка release bundle.

### `RESET_APP_DATA.bat`
Safe reset profile helper.

## 7. Каталоги и артефакты

Типовые каталоги:
- `build/`
- `dist/`
- `vendor/wheels/`

Build должен явно сообщать:
- где итоговый артефакт;
- folder-based это build или one-file;
- что именно собралось.

## 8. Offline dependencies

Wheel-cache нужен для:
- reproducible builds;
- работы без сети;
- контроля версий;
- контроля хэшей.

Правильный порядок:
1. очистить старые wheels
2. скачать pinned deps
3. сформировать manifest
4. проверить files / versions / hashes
5. только потом запускать build

## 9. Основной сценарий сборки

1. проверить Windows environment;
2. подготовить offline deps, если нужно;
3. запустить `build.bat` или `BUILD_RELEASE.bat`;
4. дождаться install and packaging;
5. проверить output;
6. прогнать smoke-check.

## 10. Поведение build-скриптов

Скрипты должны:
- печатать шаги;
- печатать понятные ошибки;
- сообщать итог success/failure;
- явно показывать путь к артефакту.

## 11. Типовые ошибки

- не найден `requirements-pinned.txt`
- не найден `manifest.json`
- отсутствует wheel-файл
- hash mismatch
- PyInstaller not available
- artifact built but does not start

Для каждой такой ошибки:
- не игнорировать;
- не “чинить наугад”;
- сначала восстановить корректный build environment.

## 12. First-run после сборки

После packaged build приложение должно:
- создать профиль;
- создать settings;
- открыть/создать DB;
- подготовить нужные папки;
- стартовать без ручного вмешательства.

## 13. Clean-machine validation

На чистой Windows-машине нужно проверить:
- запуск;
- first-run;
- основные разделы;
- sample import;
- export;
- relaunch.

## 14. Минимальный post-build smoke

После build нужно убедиться, что:
- артефакт реально существует;
- приложение запускается;
- first-run проходит;
- settings работают;
- основные экраны открываются;
- export работает;
- логи создаются.

## 15. Что не считать успешной сборкой

Недостаточно, если:
- PyInstaller не упал;
- появился `dist/`;
- есть exe.

Build successful только если:
- packaged app starts;
- runtime paths valid;
- first-run works;
- smoke passes.

## 16. Итог

Build-document finished только если:
- по нему можно реально собрать релиз;
- offline build описан;
- типовые ошибки описаны;
- clean-machine path описан;
- документ согласован с текущей build-базой проекта.

# Master Plan — Part 2B
## Packaging, One-File EXE & Offline Build

**Редакция пакета:** v3  
**Связанный индекс:** `00_INDEX.md`


## 1. Назначение документа

Этот документ фиксирует всё, что связано с:
- packaging;
- one-file exe;
- offline build;
- release UX;
- build metadata;
- release bundle;
- first-run после сборки.

## 2. Роль packaging-блока

Packaging нужен не для “красивой упаковки”, а чтобы продукт реально можно было:
- собрать;
- передать;
- запустить;
- сопровождать;
- восстанавливать.

## 3. Целевой результат

Главная цель:
- пользователь получает один основной exe;
- при необходимости — release bundle с документацией и служебными файлами;
- без отдельной инфраструктуры и сложной установки.

## 4. One-file стратегия

One-file нужен, чтобы:
- упростить запуск;
- упростить распространение;
- уменьшить количество файлов, которые пользователь может потерять.

Но one-file нельзя делать как косметику.  
Нужно заранее зафиксировать:
- resource strategy;
- profile/data outside exe;
- first-run behavior;
- diagnostics behavior;
- build info visibility.

## 5. Resource strategy

Нужен единый слой доступа к ресурсам для:
- dev mode;
- packaged mode;
- one-file mode.

### Встроенные ресурсы
- icons;
- bundled templates;
- fallback FAQ;
- internal defaults.

### Пользовательские данные
- DB;
- settings;
- branding;
- exports;
- notes;
- attachments;
- logs;
- restore points.

Принцип:
- user data вне exe;
- bundled resources внутри packaging layer.

## 6. Политика хранения пользовательских данных

Нужно разделять:
- постоянные данные;
- конфигурацию;
- кэш и временные данные;
- exports;
- attachments;
- logs.

## 7. Build metadata и версия

Нужно фиксировать:
- app version;
- build timestamp;
- build revision marker;
- build type;
- packaging mode;
- schema version.

Должно быть видно:
- в About;
- в diagnostics;
- в startup logs;
- при необходимости в export metadata.

## 8. Offline build policy

Build должен быть возможен без интернета, если wheel-cache уже подготовлен.

Для этого нужны:
- pinned requirements;
- wheel-cache;
- manifest;
- SHA validation;
- понятная процедура обновления кэша.

Manifest должен хранить:
- package;
- version;
- filename;
- sha256;
- generation timestamp;
- optional source marker.

Перед build нужно валидировать:
- наличие всех пакетов;
- наличие всех файлов;
- совпадение версий;
- совпадение хэшей.

## 9. Bat-скрипты

Finished-модель должна предусматривать:
- `BUILD_RELEASE.bat`
- `RUN_APP.bat`
- `PREPARE_OFFLINE_DEPS.bat`
- `SMOKE_TEST.bat`
- `RESET_APP_DATA.bat`
- `PACK_RELEASE.bat`

Каждый должен:
- печатать понятные шаги;
- печатать понятные ошибки;
- завершаться понятным exit code.

## 10. First-run после сборки

На первом запуске packaged build должен:
- создать профиль;
- создать settings;
- создать/открыть DB;
- подготовить нужные папки;
- открыть приложение без ручной помощи.

Нельзя считать нормой:
- ручное создание папок;
- ручное копирование ресурсных файлов;
- silent crash.

## 11. Release quality gates

### Build gate
- build passes;
- artifact produced;
- logs available.

### Runtime gate
- app starts;
- first-run works;
- resources available;
- user data outside exe.

### Functional smoke gate
- import works on sample data;
- recalc works;
- export works;
- restart works.

### UX gate
- bat scripts понятны;
- error messages понятны;
- result artifact easy to find.

## 12. Release bundle

Release bundle может содержать:
- main exe;
- quick start;
- release notes;
- user/admin docs.

В bundle не должно быть:
- dev мусора;
- raw build intermediates;
- лишних temp artifacts.

## 13. Типовые packaging-проблемы

Нужно заранее страховаться от:
- missing bundled resources;
- broken relative paths;
- inconsistent wheel-cache;
- unclear build metadata;
- broken first-run.

## 14. Тестирование packaging-блока

- path helpers;
- manifest validation;
- build metadata formatting;
- offline build smoke;
- packaged first-run;
- clean-machine acceptance.

## 15. DoD packaging-блока

Блок finished только если:
- one-file build reproducible;
- offline build reproducible;
- resource strategy unified;
- user data separated from bundled resources;
- first-run works on clean machine;
- release bundle ready;
- build metadata visible;
- smoke checks pass.

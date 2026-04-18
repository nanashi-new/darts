# Admin Guide
## Руководство администратора и сопровождающего

**Редакция пакета:** v3  
**Связанный индекс:** `00_INDEX.md`


## 1. Для кого документ

Для человека, который:
- сопровождает приложение;
- отвечает за профиль данных;
- собирает релизы;
- проверяет build/release;
- следит за нормативами, логами и recovery path.

## 2. Роль администратора

Администратор отвечает за:
- рабочий профиль;
- настройки и критичные пути;
- нормативы;
- build / release;
- wheel-cache;
- diagnostics / logs;
- backup / recovery;
- массовые операции.

## 3. Что уже есть как foundation

Уже есть:
- settings/profile layer;
- settings UI with norms path and service actions;
- audit foundation;
- build foundation;
- documented offline policy.

## 4. Модель эксплуатации

Система состоит из:
- исполняемого файла;
- пользовательского профиля;
- локальной БД;
- настроек;
- нормативов;
- logs;
- exports;
- attachments;
- diagnostics / recovery;
- build/release layer.

Для эксплуатации не требуются:
- PostgreSQL;
- pgAdmin;
- Docker;
- backend.

## 5. Что именно сопровождает администратор

- профиль данных;
- settings;
- DB;
- norms file;
- import profiles;
- logs;
- exports;
- backups / restore points;
- build artifacts;
- release bundle.

## 6. Профиль данных

Администратор должен понимать:
- где лежит профиль;
- где settings;
- где DB;
- где logs;
- где exports;
- где attachments;
- что сбрасывается reset profile.

Нельзя:
- бессистемно править профиль;
- удалять профиль без backup;
- путать user data и build artifacts.

## 7. Настройки и конфигурация

Уже доступно:
- path to norms;
- open norms folder;
- recalc all;
- merge duplicates.

Критичные действия в настройках нужно выполнять:
- осознанно;
- лучше после backup;
- с пониманием audit/recovery consequences.

## 8. Обновление нормативов

Базовый сценарий:
1. подготовить новый norms file;
2. проверить его;
3. обновить path или controlled replacement;
4. убедиться, что приложение видит файл;
5. при необходимости выполнить recalc;
6. проверить контрольные сценарии.

## 9. Import profiles и сложные импорты

Администратор должен:
- помогать настраивать profiles;
- понимать нестандартные файлы;
- удалять устаревшие profiles;
- помогать с repeated ambiguous imports.

## 10. Массовые действия

### Recalc all
Перед ним желательно:
- backup;
- понимание scope changes;
- recovery path.

### Merge duplicates
Перед ним:
- убедиться, что это реальные дубли;
- понимать impacted entities;
- иметь rollback path.

### Batch export
Проверять:
- scope;
- output path;
- количество файлов;
- journal summary.

## 11. Журнал и аудит

Администратор должен:
- уметь открыть журнал;
- фильтровать события;
- экспортировать лог;
- использовать audit при разборе проблем.

## 12. Логи и diagnostics

Администратор должен знать:
- где логи;
- как собрать diagnostics;
- как использовать self-check;
- как связать проблему с version/build/profile context.

## 13. Backup и restore

Backup нужен перед:
- mass recalc;
- tournament delete;
- merge duplicates;
- large correction;
- migration;
- reset profile.

Restore point нужен как штатный safety net, а не как исключение.

## 14. Reset profile и аварийное восстановление

Reset profile:
- не первая реакция на любую ошибку;
- должен выполняться через safe flow;
- должен сохранять backup;
- не должен подменять нормальную диагностику.

## 15. Build и release

Администратор должен:
- подготовить offline deps;
- проверить manifest;
- запустить build;
- проверить runtime;
- прогнать smoke;
- собрать bundle;
- сделать clean-machine validation.

## 16. Wheel-cache и offline build

Нужно понимать:
- где wheel-cache;
- как он обновляется;
- почему manifest и hash mismatch нельзя игнорировать.

Правильный порядок:
1. update wheel-cache
2. validate manifest
3. check pinned requirements
4. run build
5. validate result

## 17. Clean-machine validation

На чистой Windows-машине нужно проверить:
- запуск;
- first-run;
- основные разделы;
- sample import;
- export;
- relaunch.

## 18. Типовые проблемы

- build does not start;
- packaged app does not run;
- norms not found;
- after mass action data looks wrong;
- import unstable.

Во всех случаях:
- сначала audit/logs/diagnostics;
- потом risky recovery actions.

## 19. Минимальный admin checklist

Администратор должен быть уверен, что:
- приложение запускается;
- профиль создаётся;
- settings доступны;
- norms path correct;
- audit works;
- import/export works;
- build reproducible;
- recovery path understandable.

## 20. Итог

Admin guide finished, если:
- по нему можно сопровождать систему без чтения исходников;
- по нему понятно, где живут данные;
- по нему можно обновлять norms и делать build/release;
- по нему понятны backup, diagnostics и recovery.

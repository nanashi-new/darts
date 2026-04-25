# Recovery Guide
## Руководство по восстановлению и разбору проблем

**Редакция пакета:** v3  
**Связанный индекс:** `00_INDEX.md`


## 1. Назначение

Документ описывает safe recovery path при:
- broken import;
- bad recalc;
- failed merge;
- broken export;
- startup problems;
- profile corruption;
- build/runtime issues.

## 2. Базовый принцип

Сначала понять проблему.  
Потом выбрать наименее разрушительный recovery path.  
И только потом делать reset или restore.

## 3. Что уже есть как foundation

Уже можно опираться на:
- local profile model;
- журнал;
- operational recalc path;
- build/release discipline;
- audit export in TXT.

## 4. Как понимать тип проблемы

### Type A — обычная рабочая ошибка
Например:
- import issue;
- one tournament issue;
- export error.

### Type B — серьёзная operational ошибка
Например:
- mass recalc changed too much;
- bad merge;
- bad correction after publish.

### Type C — startup/profile failure
Например:
- app does not start;
- broken settings;
- DB open failure;
- failed migration.

### Type D — build/release issue
Например:
- build failed;
- packaged app broken;
- resources missing after build.

## 5. Общее правило действий

1. не удалять данные сразу;
2. зафиксировать симптом;
3. открыть журнал;
4. определить последнюю важную операцию;
5. понять scope;
6. выбрать least destructive path;
7. только потом correction / restore / reset.

## 6. Первый шаг — журнал

Журнал — первая точка разбора, потому что он помогает понять:
- последнюю операцию;
- last warnings/errors;
- import/recalc/export events.

Если проблема серьёзная, лог стоит экспортировать сразу.

## 7. Если проблема в импорте

Что делать:
- проверить файл;
- проверить лист/таблицу;
- проверить profile;
- проверить mapping;
- проверить warnings/errors;
- проверить matching;
- при необходимости сохранить как draft.

Не нужен reset profile, если проблема локальна только в одном import flow.

## 8. Если проблема в пересчёте

Что делать:
- открыть журнал;
- найти recalc summary;
- оценить warnings/errors;
- понять, проблема локальная или массовая;
- при массовой проблеме перейти к recovery-aware сценарию;
- не запускать новые массовые действия поверх сломанного состояния.

## 9. Если проблема в merge duplicates

Что делать:
- не делать новые массовые действия;
- открыть журнал;
- определить affected entities;
- использовать correction или restore depending on scope.

## 10. Если проблема в экспорте

Что делать:
- проверить журнал;
- проверить output path;
- проверить, не открыт ли файл;
- попробовать другую папку;
- при batch export сверить количество созданных файлов.

## 11. Если приложение не запускается

Что делать:
1. не удалять профиль сразу;
2. понять, запускалось ли раньше;
3. понять, после какого действия началась проблема;
4. проверить логи;
5. проверить profile/settings;
6. использовать diagnostics if available;
7. только потом safe reset or restore.

## 12. Safe reset profile

Reset profile нужен, если:
- профиль повреждён;
- startup стабильно ломается именно из-за профиля.

Правильный safe flow:
1. сохранить backup старого профиля;
2. зафиксировать reason;
3. выполнить reset через официальный сценарий;
4. проверить new first-run;
5. переносить обратно только безопасные данные.

Нельзя:
- просто удалять профиль руками без backup;
- использовать reset вместо normal diagnosis.

## 13. Restore point recovery

Restore лучше, если:
- операция затронула много данных;
- есть понятная точка “до проблемы”;
- ручной repair опаснее.

Перед restore:
- понять scope rollback;
- убедиться, что restore point правильный;
- сохранить diagnostics if needed.

После restore:
- проверить запуск;
- проверить ключевые сущности;
- проверить рейтинг и турниры;
- не продолжать risky actions без проверки.

## 14. Если проблема связана с нормативами

Проверить:
- правильный ли norms file;
- действительно ли path обновлён;
- запускался ли recalc;
- expected ли изменение результатов;
- нужен ли rollback после массового неверного изменения.

## 15. Если проблема связана со сборкой/релизом

Что делать:
- открыть `BUILD_WINDOWS.md`;
- проверить requirements / wheel-cache / manifest;
- проверить build output;
- проверить clean-machine scenario;
- отделять build problem от runtime profile problem.

## 16. Diagnostic bundle

Diagnostics стоит собирать, если:
- проблема повторяется;
- нужна помощь другого человека;
- перед reset/restore;
- проблема массовая;
- проблема связана со стартом.

## 17. Практические сценарии

### Import испортил турнир
- stop;
- open journal;
- inspect preview/import summary;
- decide correction vs re-import vs restore.

### После recalc all всё изменилось
- inspect journal;
- understand scope;
- compare with expected;
- use recovery-aware path.

### После обновления приложение не запускается
- do not delete profile;
- inspect logs;
- inspect profile/settings;
- safe reset if really needed;
- collect diagnostics.

### Export fails
- inspect journal;
- inspect path and locks;
- try different destination;
- save diagnostics if repeated.

## 18. Чего делать нельзя

- удалять профиль без backup;
- игнорировать warnings;
- делать несколько risky actions подряд без проверки;
- смешивать correction, merge, restore и reset без понимания порядка;
- хаотично подменять файлы.

## 19. Минимальный recovery-checklist

Перед жёстким действием проверить:
- открыт ли журнал;
- понятна ли последняя проблемная операция;
- локальная это проблема или массовая;
- нужен ли correction вместо reset;
- есть ли restore point;
- можно ли собрать diagnostics;
- понятны ли последствия следующего шага.

## 20. Итог

Recovery можно считать завершённым, если:
- пользователь снова может работать;
- состояние проверено;
- причина хотя бы примерно понятна;
- risk of repeated failure reduced;
- diagnostics/audit preserved for serious cases.

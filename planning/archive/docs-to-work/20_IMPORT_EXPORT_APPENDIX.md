# Appendix C
## Import/Export Appendix
### Практические правила импорта, mapping, форматы файлов, export scopes и naming conventions

**Редакция пакета:** v3  
**Статус документа:** приложение к мастер-плану  
**Назначение:** собрать в одном месте практические правила импорта и экспорта: входные форматы, expected columns, mapping rules, import profile behavior, warnings/errors, export scopes, naming conventions и grouped export cases.

**Этот документ является логическим продолжением:**
- `05_MASTER_PLAN_PART_2_OPERATIONS_RELEASE.md`
- `07_MASTER_PLAN_PART_2B_PACKAGING_OFFLINE_BUILD.md`
- `10_MASTER_PLAN_PART_3_IMPLEMENTATION_ROADMAP.md`
- `12_BUILD_WINDOWS.md`
- `13_USER_GUIDE.md`

---

# 1. Назначение документа

Этот документ нужен, чтобы:
- не держать правила импорта/экспорта только в коде;
- уменьшить число ошибок в реальных operational flows;
- унифицировать ожидания от Excel-файлов, import profiles и export outputs;
- дать опору для import tests и release validation.

Он не заменяет пользовательский гайд и не фиксирует все UI-экраны. Его задача — быть практическим reference по import/export behavior.

---

# 2. Общая модель импорта

## 2.1. Что такое import в этой системе

Import — это не просто открытие xlsx. Это full flow:
1. выбор источника;
2. анализ структуры;
3. table detection;
4. header detection;
5. profile matching;
6. column mapping;
7. player matching;
8. preview;
9. warnings/errors;
10. apply into tournament draft/review flow.

## 2.2. Что уже есть как база

В текущей базе уже есть:
- Excel parsing;
- multi-table support;
- confidence-based recognition;
- import profiles;
- player matching foundation;
- folder import foundation;
- tournament/results creation path.

Это означает, что appendix должен усиливать already existing foundation, а не предполагать import from zero.

---

# 3. Поддерживаемые import sources

## 3.1. Основные источники

В finished import model нужно поддерживать:
- один Excel-файл (`.xlsx`)
- несколько Excel-файлов для одного турнира
- отдельный файл мест
- папку с набором файлов
- повторный импорт исправленного протокола

## 3.2. Что считать одной import session

Одна import session — это один целостный запуск import flow с одним итоговым результатом preview/apply, даже если в нём несколько файлов.

---

# 4. Поддерживаемые таблицы и листы

## 4.1. Общий принцип

Файл может содержать:
- один лист с одной таблицей;
- один лист с несколькими таблицами;
- несколько листов;
- заголовки не в первой строке.

## 4.2. Что должен уметь parser

Parser должен:
- находить candidate tables;
- определять headers;
- определять possible data block range;
- вычислять confidence;
- уметь показать preview найденных блоков.

---

# 5. Обязательные поля для child tournament import

Ниже приводится logical expected set. Названия колонок в файле могут отличаться, но import profile/mapping должен уметь их связать.

## 5.1. Обязательные логические поля

Минимально:
- `player_full_name`
- `birth_date` или sufficient birth-year key if accepted by current workflow
- `gender` (если это требуется по структуре турнира или не может быть выведено из category scope)
- category-related context or data sufficient to determine it
- one or more discipline values (если child classification mode используется)
- `place` (если place points применяются)

## 5.2. Допустимые дополнительные поля

- coach name
- club/section
- sheet-level category marker
- row-level comments
- import-specific auxiliary columns

## 5.3. Missing required fields

Если отсутствуют логически обязательные поля, import flow должен:
- показать missing fields;
- не silently применять неверную интерпретацию;
- предложить mapping correction;
- при необходимости блокировать apply.

---

# 6. Обязательные поля для adult manual / adult assisted import

Если adult data импортируется, expected logical set обычно включает:
- `player_full_name`
- birth-related identity data where needed
- `gender` where needed for split scopes
- `place`
- `points_total` or equivalent adult scoring fields

Adult import не должен пытаться притвориться child classification file.

---

# 7. Column mapping rules

## 7.1. Общий принцип

Mapping связывает реальные headers файла с логическими полями системы.

## 7.2. Что должен поддерживать mapping

- auto-match by known aliases
- profile-based match
- manual override by user
- save as profile
- missing required field detection
- conflict detection

## 7.3. Какие aliases стоит поддерживать

Например, для одного logical field возможны разные headers:
- ФИО / Игрок / Участник / Name / Full Name
- ДР / Дата рождения / Год рождения / Birth Date
- Место / Place / Итоговое место

Конкретный alias set должен храниться как данные конфигурации/import profiles, а не быть спрятан только в UI.

---

# 8. Import profiles

## 8.1. Что хранит профиль

Import profile должен хранить:
- имя профиля
- описание
- required fields model
- column mapping
- confidence hints
- optional table-detection hints
- tournament type defaults

## 8.2. Как profile применяется

При новом импорте система должна:
- сравнить headers и структуру с profiles;
- оценить confidence;
- предложить best matching profile;
- позволить пользователю подтвердить или изменить выбор.

## 8.3. Когда профиль устарел

Признаки устаревшего профиля:
- часто появляются missing fields;
- confidence заметно упал;
- требуется постоянная ручная правка mapping;
- source files изменили структуру.

---

# 9. Player matching rules

## 9.1. Общая модель

Player matching должен использовать:
- normalized full name
- birth date / birth year key
- existing player candidates
- remembered match rules

## 9.2. Разрешённые исходы matching step

- unique match found
- ambiguous candidates shown
- user selected existing player
- user created new player
- user cancelled import step
- remembered rule saved

## 9.3. Что нельзя делать

Нельзя silently матчить игрока с низкой уверенностью без явного контроля.

---

# 10. Import warnings and errors

## 10.1. Warnings

Warnings — это проблемы, которые не всегда блокируют import apply.

Типовые warnings:
- low confidence mapping
- ambiguous matching resolved manually
- missing optional fields
- unusual numeric values
- duplicate-like rows
- partial tournament information

## 10.2. Errors

Errors — это блокирующие или тяжёлые проблемы.

Типовые errors:
- no readable table found
- required columns missing
- invalid file type
- fatal parsing failure
- impossible category resolution
- irrecoverable tournament data inconsistency

## 10.3. Требование к reporting

Warnings/errors должны быть:
- grouped;
- attributable to row/column/stage where possible;
- exportable in import report;
- visible before apply.

---

# 11. Import preview

## 11.1. Что обязательно должно входить в preview

- detected source tables
- applied mapping/profile
- players to be created
- players to be matched
- category on tournament date
- discipline interpretations
- place points interpretation
- tournament totals preview
- rating impact preview
- warnings/errors summary

## 11.2. Зачем нужен preview

Preview нужен, чтобы import не был irreversible black box.

---

# 12. Import report

## 12.1. Что должен содержать import report

Минимально:
- files processed
- tables processed
- rows read
- rows imported
- rows skipped
- players created
- players matched manually
- warnings count
- errors count
- apply status
- created/updated tournament context

## 12.2. Формат import report

Report может храниться:
- в DB as import session metadata
- и/или как exportable text/json artifact

---

# 13. Draft vs apply semantics

## 13.1. Draft import

Draft import означает:
- imported data prepared
- tournament not yet officially published
- current official rating not yet updated
- user can return to review

## 13.2. Apply / publish-related import

Apply означает:
- data accepted into tournament operational state
- next steps may include review/confirm/publish
- import changes become formal part of tournament workflow

Import itself must not silently equal publish.

---

# 14. Export model

## 14.1. Основные export scopes

В finished-системе должны поддерживаться:
- current rating export
- grouped rating export
- tournament summary export
- tournament protocol export
- batch export
- internal report export
- audit log export
- diagnostics bundle export

## 14.2. Основные форматы

Основные форматы:
- PDF
- XLSX

Дополнительные форматы по мере готовности:
- CSV
- DOCX
- image/PNG where operationally useful
- QR where explicitly introduced later

---

# 15. Export naming conventions

## 15.1. Общий принцип

Имена export files должны быть:
- читаемыми человеком;
- воспроизводимыми;
- пригодными для сортировки;
- не слишком длинными;
- по возможности включать дату/scope.

## 15.2. Рекомендуемая структура имени

Рекомендуется использовать:
- тип export
- scope / category / league / tournament
- date or effective date
- optional version suffix

Примеры структуры:
- `rating_children_boys_u14_2026-04-18.pdf`
- `tournament_monthly_open_2026-03-15.xlsx`
- `league_premier_snapshot_2026-04-18.pdf`

## 15.3. Что нежелательно

- `new.xlsx`
- `final_final2.pdf`
- `export(1).xlsx`
- names without date/scope when ambiguity likely

---

# 16. Grouped export rules

## 16.1. Что такое grouped export

Grouped export — это export, где несколько категорий/scope’ов собираются в один logical output package or one multi-section output.

## 16.2. Где grouped export особенно полезен

- children ratings by categories
- all categories for one event/period
- league outputs
- print packs

## 16.3. Decision table

Перед grouped export система должна знать:
1. Какие scopes включены?
2. В каком порядке они идут?
3. Какие naming conventions применяются?
4. Это один файл или пакет файлов?
5. Какие headers/section titles печатаются?

---

# 17. Export metadata

## 17.1. Что желательно добавлять в export metadata

- generated at
- scope
- tournament/date context
- rolling N where relevant
- app version/build info where useful

## 17.2. Зачем это нужно

Это помогает:
- разбирать спорные exports;
- сравнивать outputs между релизами;
- повышать explainability.

---

# 18. Print-friendly rules

## 18.1. Print mode должен учитывать

- читаемые заголовки
- даты
- grouping sections
- column widths
- перенос строк
- отсутствие мусорных UI-элементов

## 18.2. Print-friendly и export не одно и то же

PDF/print output должен быть удобен для печати, а не просто быть скриншотом таблицы.

---

# 19. Export failure handling

## 19.1. Типовые причины ошибок

- invalid output path
- file locked by another program
- missing permissions
- invalid format handler
- broken source data state

## 19.2. Что должен делать export flow

- показывать понятную ошибку
- писать audit/log event
- не silently fail
- по возможности позволять выбрать другой output path

---

# 20. Import/export storage rules

## 20.1. Импортные исходники

Source files могут храниться:
- как attachments to tournament
- как temporary processing files
- как part of import session context

## 20.2. Экспортные результаты

Export outputs должны храниться в dedicated export directory и не смешиваться с bundled assets or DB files.

---

# 21. Матрица обязательных import/export тестов

## 21.1. Import

Обязательно тестировать:
- one-file import
- multi-table import
- folder import
- import profile application
- manual match flow
- preview generation
- import report generation
- draft import behavior

## 21.2. Export

Обязательно тестировать:
- rating export PDF/XLSX
- tournament export
- grouped export
- batch export
- print-friendly output generation
- export failure handling

---

# 22. Что должно быть данными, а не кодом

Данными/config должны оставаться:
- import aliases
- profile definitions
- mapping hints
- output naming templates where configurable
- grouped export presets where useful

Не всё это должно быть захардкожено в UI or business logic.

---

# 23. Критерий завершения приложения

Этот appendix считается finished только если:
- описаны supported import sources and steps;
- перечислены logical required fields;
- зафиксированы mapping/profile/matching rules;
- зафиксированы warning/error categories;
- описаны export scopes and formats;
- описаны naming conventions and grouped export behavior;
- документ пригоден как практический reference для разработки, QA и администрирования.

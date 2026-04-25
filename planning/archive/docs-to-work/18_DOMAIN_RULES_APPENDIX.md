# Appendix A
## Domain Rules Appendix
### Формальные доменные правила, инварианты и decision tables

**Редакция пакета:** v3  
**Статус документа:** приложение к мастер-плану  
**Назначение:** собрать в одном месте формальные предметные правила системы: категории, переходы, турниры, рейтинги, лиги, corrections, explainability-правила и набор decision tables, по которым можно проверять реализацию.

**Этот документ является логическим продолжением:**
- `01_PRODUCT_SCOPE.md`
- `03_MASTER_PLAN_PART_1_FOUNDATION.md`
- `04_MASTER_PLAN_PART_1A_TOURNAMENT_EXPANSION.md`
- `05_MASTER_PLAN_PART_2_OPERATIONS_RELEASE.md`
- `10_MASTER_PLAN_PART_3_IMPLEMENTATION_ROADMAP.md`

---

# 1. Назначение документа

Основной мастер-план описывает архитектуру и finished-сценарии. Это приложение нужно для другого:
- формально зафиксировать предметные правила;
- отделить строгие правила от пользовательского UI;
- уменьшить риск разных трактовок одной и той же логики;
- дать опору для domain tests, regression checks и ручной верификации.

Этот документ не должен подменять официальный нормативный источник. Если официальный регламент или утверждённый `norms.xlsx` меняется, именно они являются источником численных значений. Этот appendix определяет **модель применения правил**, decision tables и обязательные инварианты.

---

# 2. Источники истины для доменных правил

## 2.1. Приоритет источников

При конфликте источников приоритет должен быть таким:
1. утверждённый официальный регламент / решение организатора;
2. утверждённый `norms.xlsx` как операционный источник численных таблиц;
3. формально согласованный мастер-план;
4. текущая реализация кода.

## 2.2. Что нельзя делать

Нельзя:
- считать код единственным источником доменной истины;
- silently менять правила в коде без обновления нормативного источника;
- выпускать новую сборку с изменёнными доменными таблицами без фиксации изменения.

---

# 3. Базовые доменные инварианты

## 3.1. Инварианты по игроку

1. Игрок существует независимо от текущего рейтинга.
2. Игрок может участвовать в нескольких исторических категориях на разных турнирах.
3. Исправление данных игрока не должно silently переписывать исторический контекст без traceable event.
4. Merge duplicates не должен разрушать explainability истории игрока.

## 3.2. Инварианты по категории

1. Категория на турнир определяется по **дате турнира** и **дате рождения**.
2. Текущая категория игрока и историческая категория на конкретный турнир могут различаться.
3. Исторические результаты не должны пересчитываться по "сегодняшней" категории.
4. Child и adult domain modes должны оставаться логически разделёнными.

## 3.3. Инварианты по турниру

1. Турнир — first-class сущность с жизненным циклом.
2. Турнир не равен одному импортированному файлу.
3. Турнир влияет на официальный рейтинг только после явной публикации.
4. Dangerous operations над турниром должны быть traceable и recoverable.

## 3.4. Инварианты по рейтингу

1. Current rating должен быть воспроизводим из турнирных данных и доменных правил.
2. History/snapshots не должны теряться после corrections.
3. Rolling basis должен быть объяснимым для каждой позиции рейтинга.
4. Adult ratings и league ratings не должны быть disguised child-mode variants.

## 3.5. Инварианты по explainability

1. Любое важное ручное изменение должно оставлять formal trace.
2. Notes не заменяют audit.
3. Correction after publish не должен происходить silently.
4. Broken recovery path не должен уничтожать данные без осознанного решения.

---

# 4. Категории и возрастные правила

## 4.1. Общая модель

Категория определяется как функция от:
- даты рождения игрока;
- даты турнира;
- пола;
- approved category rules.

## 4.2. Decision table для определения категории

При вычислении категории система должна последовательно ответить на вопросы:
1. Является ли игрок ребёнком или взрослым на дату турнира?
2. Какой возрастной диапазон соответствует возрасту на дату турнира?
3. Какие категории допустимы для данного пола?
4. Требуется ли отдельная child classification logic?
5. Допустима ли лига или adult mode для этого турнира?

## 4.3. Граничные сценарии

Обязательно должны быть обработаны и протестированы:
- турнир в день рождения;
- турнир на следующий день после перехода;
- исправление даты рождения постфактум;
- отсутствие даты рождения;
- неоднозначный возрастной кейс;
- migration of old data where category had been stored implicitly.

## 4.4. Что должно быть configurable

Через нормативный источник должны определяться:
- список категорий;
- возрастные границы;
- gender applicability;
- discipline availability;
- child/adult flags;
- default rolling window, если оно зависит от category scope.

---

# 5. Child mode: дисциплины, разряды и classification points

## 5.1. Общая модель

В child mode итог формируется из двух крупных блоков:
- classification points;
- place points.

## 5.2. Classification points

Classification points должны вычисляться на основе:
- результатов по дисциплинам;
- правил перевода результата в разряд/ранг;
- правил перевода разряда/ранга в очки.

## 5.3. Decision table для child classification

Для каждого игрока в детском турнире система должна определить:
1. Какие дисциплины для него допустимы в этой категории?
2. Какие значения дисциплин получены?
3. Какой rank/разряд соответствует каждому значению?
4. Какие points_from_rank получаются по каждой дисциплине?
5. Как агрегируются discipline-level points в classification total?

## 5.4. Строгое правило по численным таблицам

Численные таблицы:
- перевода результата дисциплины в rank/разряд;
- перевода rank/разряда в очки;
- special cases;

не должны быть «зашиты» в документацию вручную, если их утверждённый источник — `norms.xlsx` или официальный регламент. Они должны оставаться **данными**, а не случайным кодом.

## 5.5. Обязательные special cases

Система должна уметь явно обрабатывать:
- missing discipline value;
- invalid numeric value;
- category without discipline;
- manual override rank;
- partial import where some disciplines are absent;
- corrected protocol after initial publish.

---

# 6. Place points

## 6.1. Общая модель

Place points — это отдельный доменный блок, независимый от child classification.

## 6.2. Decision table для place points

Для расчёта place points система должна определить:
1. Есть ли place для игрока?
2. Валиден ли place как число?
3. Допустим ли place для выбранного tournament type / category scope?
4. Какой points_from_place соответствует этому place по утверждённой таблице?
5. Есть ли manual override по place или points_from_place?

## 6.3. Особые случаи

Нужно явно обрабатывать:
- place отсутствует;
- place задан текстом/некорректным форматом;
- дублирующиеся places;
- place corrections after publish;
- imported place из отдельного файла мест;
- manual entry взрослых турниров.

---

# 7. Итог турнира по игроку

## 7.1. Общая формула

Для каждого игрока система должна формировать tournament total как составную величину:
- classification total (если применимо)
- plus place total
- plus/minus controlled overrides where formally allowed

## 7.2. Decision table для tournament total

1. Определить tournament mode: child / adult / league.
2. Определить category_on_tournament_date.
3. Определить classification applicability.
4. Рассчитать classification total.
5. Рассчитать place total.
6. Применить controlled overrides.
7. Сформировать grand total.
8. Сохранить explainable breakdown.

## 7.3. Инвариант explainability

У grand total всегда должен быть объяснимый breakdown:
- из чего получен classification total;
- как получен place total;
- были ли overrides;
- почему игрок включён или не включён в rating scope.

---

# 8. Adult mode rules

## 8.1. Общая модель

Adult mode не использует child classification logic как fallback.

## 8.2. Adult scoring decision table

Для adult tournament система должна определить:
1. Является ли турнир adult mode?
2. Вводятся ли очки вручную?
3. Вводятся ли места вручную?
4. Какие rating scopes affected: overall, men, women?
5. Есть ли league context?

## 8.3. Инварианты adult mode

1. Нельзя silently использовать child tables in adult flow.
2. Adult overall and split ratings должны быть согласованы между собой.
3. Manual overrides должны быть видны и audit-traceable.

---

# 9. League rules

## 9.1. Общая модель

Лиги — отдельный доменный контур.

## 9.2. Decision table для league flow

Для league tournament система должна определить:
1. Турнир относится к Премьер или Первой лиге?
2. Какие игроки участвуют в текущем league scope?
3. Какие ranking changes происходят внутри лиги?
4. Есть ли кандидаты на transfer?
5. Какой transfer preview показывается до publish?
6. Какие transfers подтверждаются после publish?

## 9.3. Инварианты по лигам

1. League flow не должен быть простым фильтром общего рейтинга.
2. Transfer decisions должны быть traceable.
3. League history должна быть доступна после corrections.

---

# 10. Rolling rating rules

## 10.1. Общая модель

Rolling rating строится из последних `N` турниров в конкретном rating scope.

## 10.2. Decision table для rolling basis

Для каждого игрока и scope система должна определить:
1. Какие турниры релевантны scope?
2. Какие из них валидны для учёта после publish/correction?
3. Какой сортировкой определяется "последние N"?
4. Что делать, если турниров меньше, чем `N`?
5. Как выполняется tie-break between equal points?

## 10.3. Инварианты rolling basis

1. Rolling basis должен быть детерминированным.
2. Changing `N` должно давать объяснимый и воспроизводимый результат.
3. Published correction должен корректно обновлять rolling basis.
4. Удаление турнира должно приводить к корректному пересчёту basis.

---

# 11. History and snapshots rules

## 11.1. Общая модель

History и snapshots — не побочные данные, а first-class domain layer.

## 11.2. Когда создаётся snapshot

Snapshot должен создаваться как минимум при:
- publish tournament;
- correction after publish;
- major batch recalculation, если политика проекта требует snapshot after batch.

## 11.3. Decision table для snapshot creation

1. Есть ли publish-affecting domain change?
2. Какой rating scope affected?
3. Нужно ли создавать snapshot for current scope?
4. Какой source tournament / reason записывается?
5. Как обеспечить consistency with player history?

## 11.4. Инварианты history

1. Current rating не должен терять связь с history.
2. Snapshot должен иметь reason/source context.
3. Correction after publish должна обновлять history explainably, а не silently.

---

# 12. Tournament lifecycle rules

## 12.1. Общая state machine

Поддерживаются статусы:
- Draft
- Review
- Confirmed
- Published
- Archived
- Cancelled
- Deleted (special destructive flow)

## 12.2. Правила переходов

Разрешены только контролируемые переходы, описанные в tournament lifecycle document.

## 12.3. Инварианты lifecycle

1. Import не должен silently equal publish.
2. Published tournament нельзя редактировать как обычный draft.
3. Dangerous transitions должны быть traceable and recoverable.
4. Delete не должен происходить без явного destructive flow.

---

# 13. Correction after publish rules

## 13.1. Общая модель

Correction after publish — отдельный доменный сценарий.

## 13.2. Decision table

1. Является ли изменяемая сущность published-affecting?
2. Нужен ли formal correction flow?
3. Нужен ли reason?
4. Нужен ли restore point?
5. Какие rating scopes affected?
6. Нужно ли создавать новый snapshot?
7. Какие audit events обязательны?

## 13.3. Инварианты correction

1. Correction after publish не должен выглядеть как обычное редактирование.
2. Correction должен быть traceable.
3. Correction должен обновлять history/current согласованно.

---

# 14. Notes vs audit rules

## 14.1. Decision rule

Если действие меняет формальное состояние системы, нужен audit.  
Если действие добавляет человеческий контекст — нужен note.  
Если происходит и то и другое — нужны оба слоя.

## 14.2. Инвариант

Notes никогда не заменяют audit.  
Audit никогда не заменяет notes.

---

# 15. Recovery and dangerous actions rules

## 15.1. Когда dangerous action требует safety net

Как минимум перед такими действиями нужен recovery-aware path:
- delete tournament;
- recalc all;
- merge duplicates on large set;
- major correction after publish;
- migration.

## 15.2. Decision table

1. Является ли действие destructive или массовым?
2. Требуется ли restore point?
3. Требуется ли reason?
4. Требуется ли warning dialog?
5. Требуется ли post-action self-check?

---

# 16. Таблица обязательных доменных decision points

Ниже — компактный перечень решений, которые нельзя оставлять “на усмотрение UI”.

| Область | Обязательное решение |
|---|---|
| Категория | по дате турнира и дате рождения |
| Child classification | по нормативному источнику |
| Place points | по утверждённой таблице |
| Total | по mode-aware aggregation |
| Rolling basis | по deterministic scope-aware selection |
| Publish | только через explicit lifecycle step |
| Correction | только через controlled correction flow |
| League transfer | только через traceable transfer logic |
| Audit | обязателен для formal changes |
| Recovery | обязателен для dangerous actions |

---

# 17. Что должно быть test-driven в первую очередь

В первую очередь автоматизированно должны проверяться:
- category resolution;
- child classification mapping;
- place point conversion;
- tournament total aggregation;
- rolling basis selection;
- snapshot creation;
- transition boundaries;
- correction after publish behavior.

---

# 18. Критерий завершения приложения

Этот appendix считается finished только если:
- собраны формальные rules и decision tables;
- явно отделены данные-нормативы от логики их применения;
- перечислены доменные инварианты;
- документ пригоден как опора для domain tests, code review и ручной верификации.

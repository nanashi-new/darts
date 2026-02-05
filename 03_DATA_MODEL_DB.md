# 03 — Модель данных и встроенная база данных

Связанные документы:
- Правила и алгоритмы: [02_RULES_ALGORITHMS.md](02_RULES_ALGORITHMS.md)
- Импорт / экспорт Excel: [04_IMPORT_EXPORT_XLSX.md](04_IMPORT_EXPORT_XLSX.md)
- Архитектура: [07_ARCHITECTURE.md](07_ARCHITECTURE.md)

---

## 1. Общие принципы

- База данных **встроена в приложение**
- Используется **SQLite**
- Один файл БД (`app.db`)
- Никаких внешних серверов
- Все данные принадлежат пользователю
- БД должна легко переноситься между компьютерами

---

## 2. Основные сущности

### 2.1 Игрок (Player)

Хранит персональные данные спортсмена.

**Таблица: `players`**

| Поле | Тип | Описание |
|----|----|----|
| id | INTEGER PK | уникальный идентификатор |
| last_name | TEXT | фамилия |
| first_name | TEXT | имя |
| middle_name | TEXT | отчество (опц.) |
| birth_date | DATE | дата рождения |
| gender | TEXT | `M` / `F` |
| coach | TEXT | тренер |
| club | TEXT | клуб / школа |
| notes | TEXT | примечания |
| created_at | DATETIME | дата создания |
| updated_at | DATETIME | дата изменения |

**Индексы**
- `(last_name, first_name)`
- `birth_date`

---

### 2.2 Турнир (Tournament)

**Таблица: `tournaments`**

| Поле | Тип | Описание |
|----|----|----|
| id | INTEGER PK |
| name | TEXT | название турнира |
| date | DATE | дата проведения |
| category_code | TEXT | код категории |
| league_code | TEXT | `NULL / PREMIER / FIRST` |
| source_files | TEXT | JSON со списком импортированных файлов |
| created_at | DATETIME |
| updated_at | DATETIME |

---

### 2.3 Результат (Result)

Результаты игрока в конкретном турнире.

**Таблица: `results`**

| Поле | Тип | Описание |
|----|----|----|
| id | INTEGER PK |
| tournament_id | INTEGER FK |
| player_id | INTEGER FK |
| place | INTEGER | место |
| score_set | INTEGER | набор очков |
| score_sector20 | INTEGER | сектор 20 |
| score_big_round | INTEGER | большой раунд |
| rank_set | TEXT | разряд по набору |
| rank_sector20 | TEXT | разряд по сектору |
| rank_big_round | TEXT | разряд по большому раунду |
| points_classification | INTEGER | очки за классификацию |
| points_place | INTEGER | очки за место |
| points_total | INTEGER | итог турнира |
| calc_version | TEXT | версия алгоритма |

**Ограничения**
- `(tournament_id, player_id)` — UNIQUE
- `place >= 1 OR place IS NULL`

---

### 2.4 Кэш рейтинга (опционально)

Используется для ускорения UI.

**Таблица: `rating_cache`**

| Поле | Тип |
|----|----|
| player_id | INTEGER |
| category_code | TEXT |
| window_n | INTEGER |
| rating_points | INTEGER |
| updated_at | DATETIME |

Можно пересчитывать рейтинг на лету и не хранить кэш на первом этапе.

---

## 3. Справочные данные

### 3.1 Нормативы ЕВСК

Нормативы могут:
- храниться в отдельной таблице
- или загружаться из `.xlsx` в память при старте

Рекомендуется:
- хранить файл нормативов внутри проекта;
- иметь версию нормативов.

---

## 4. История и безопасность (v1.1)

### 4.1 Журнал изменений (audit log)

**Таблица: `audit_log`**

| Поле | Тип | Описание |
|----|----|----|
| id | INTEGER |
| entity | TEXT | таблица |
| entity_id | INTEGER |
| action | TEXT | create/update/delete |
| before | TEXT | JSON |
| after | TEXT | JSON |
| created_at | DATETIME |

---

## 5. Бэкап и перенос

- Экспорт БД в ZIP
- Импорт ZIP на другом ПК
- Проверка версии схемы
- Автоматическое обновление схемы при необходимости

---

Конец документа.

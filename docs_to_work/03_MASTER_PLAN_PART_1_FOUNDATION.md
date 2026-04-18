# Master Plan — Part 1
## Foundation

**Редакция пакета:** v3  
**Связанный индекс:** `00_INDEX.md`


## 1. Назначение документа

Этот документ фиксирует фундамент:
- архитектуру;
- слои;
- first-class сущности;
- инварианты;
- стратегию хранения;
- запреты.

Он не заменяет:
- турнирную спецификацию;
- roadmap;
- UI-спецификацию;
- эпики.

## 2. Архитектурная модель

Продукт строится как локальное desktop-приложение с четырьмя слоями:
1. UI Layer
2. Application Layer
3. Domain Layer
4. Infrastructure Layer

### UI Layer
Отвечает за:
- экраны;
- диалоги;
- navigation;
- preview;
- user actions.

UI не должен содержать доменную математику.

### Application Layer
Отвечает за:
- orchestration;
- сценарии;
- transaction-like flows;
- import/apply/publish/correction/recovery.

### Domain Layer
Отвечает за:
- категории;
- очки;
- турниры;
- рейтинги;
- snapshots;
- transitions;
- лиги;
- инварианты.

### Infrastructure Layer
Отвечает за:
- SQLite;
- files;
- settings;
- logs;
- attachments;
- backup/restore;
- imports/exports;
- build/runtime metadata.

## 3. Архитектурные запреты

Запрещено:
- держать доменную логику в UI;
- держать пользовательские данные внутри exe;
- смешивать notes и audit;
- размывать desktop nature продукта;
- подменять recovery ручной файловой магией.

## 4. First-class сущности

Finished-система должна опираться на:
- Player
- Category
- Tournament
- TournamentResult
- RatingCurrent
- RatingSnapshot / RatingHistory
- League / LeagueTransfer
- Note
- TrainingEntry
- Tag
- CustomFieldDefinition / CustomFieldValue
- Attachment
- AuditEvent
- RestorePoint

## 5. Базовая доменная модель

### Player
Базовые атрибуты:
- ФИО;
- дата рождения;
- пол;
- тренер;
- клуб/секция;
- статус.

### Category
- код;
- название;
- возрастные границы;
- пол;
- child/adult flag;
- discipline set;
- default rolling window.

### Tournament
- название;
- дата;
- тип;
- статус;
- сезон;
- серия;
- площадка;
- организатор;
- creation source.

### TournamentResult
- игрок;
- турнир;
- category_on_tournament_date;
- raw points;
- place points;
- totals;
- warnings/flags.

### RatingSnapshot
- scope;
- player;
- position;
- points;
- effective date;
- source tournament;
- rolling basis payload.

## 6. Инварианты

### Категории
- категория на турнир определяется по дате турнира и ДР;
- турнир не пересчитывается по “сегодняшней” категории;
- старая категория в истории не теряется.

### Турниры
- турнир — отдельная сущность lifecycle;
- опубликованный турнир не должен silently менять рейтинг;
- удаление турнира должно быть контролируемым.

### Рейтинг
- current rating воспроизводим;
- history не теряется;
- rolling basis объясним.

### Children / adults / leagues
- детская логика не подменяет взрослую;
- взрослая логика не зависит от детской классификации;
- лиги не сводятся к фильтру общего рейтинга.

### Explainability
- значимые ручные правки traceable;
- notes не заменяют audit;
- recovery actions traceable.

## 7. Стратегия хранения

### Встроенные ресурсы
- иконки;
- bundled templates;
- fallback FAQ;
- default assets.

### Пользовательские данные
- SQLite DB;
- settings;
- exports;
- logs;
- notes;
- attachments;
- restore points;
- branding files.

Принцип: пользовательские данные всегда вне exe.

## 8. Стратегия эволюции

Правильный порядок:
- foundation;
- tournament lifecycle;
- import and operations;
- ratings/history;
- notes/context;
- audit/recovery;
- UI/workspace;
- packaging/release.

## 9. Основные риски

- смешать UI и домен;
- оставить модель слишком бедной;
- потерять desktop nature;
- не зафиксировать инварианты;
- финализировать UI раньше логики;
- финализировать packaging раньше resource strategy.

## 10. Итоговая фиксация

Финально принимается:
- architecture = UI / Application / Domain / Infrastructure;
- tournaments, ratings, notes, audit, restore points — first-class;
- пользовательские данные вне exe;
- history и explainability обязательны;
- recovery и diagnostics — часть архитектуры, а не “потом”.

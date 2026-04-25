# 09 — План тестирования и приёмки

> Active execution order lives in [`planning/00_PRIORITY.md`](planning/00_PRIORITY.md).
> This file is a testing reference. New release/test tasks must be linked from `planning/tasks/`.

Связанные документы:
- Правила: [02_RULES_ALGORITHMS.md](02_RULES_ALGORITHMS.md)
- Импорт/экспорт: [04_IMPORT_EXPORT_XLSX.md](04_IMPORT_EXPORT_XLSX.md)
- Релизный прогон: [docs/11_RELEASE_TEST_RUN.md](docs/11_RELEASE_TEST_RUN.md)

---

## 1. Слои тестирования и pytest-маркеры

| Слой | Маркер | Что проверяет | Пример запуска |
|---|---|---|---|
| Unit | `@pytest.mark.unit` | Чистая бизнес-логика без UI и без сквозного сценария (очки, разряды, rolling). | `pytest -m unit` |
| Integration | `@pytest.mark.integration` | Взаимодействие сервисов, БД и файловой системы (импорт/пересчёт/экспорт/журнал по частям). | `pytest -m integration` |
| Release smoke | `@pytest.mark.release_smoke` | Минимальный e2e-критический путь перед релизом. | `pytest -m release_smoke` |

Рекомендуемый порядок прогона перед релизом:
1) `pytest -m unit`
2) `pytest -m integration`
3) `pytest -m release_smoke`

---

## 2. Минимальный e2e-набор (критический путь)

| ID | Сценарий | Измеримые критерии прохождения |
|---|---|---|
| E2E-01 | Импорт XLSX с 2 строками результатов | Создан турнир; в БД ровно 2 записи результатов; исключений нет. |
| E2E-02 | Пересчёт одного турнира | `tournaments_processed == 1`; `results_updated == 2`; `errors == []`. |
| E2E-03 | Пересчёт всех турниров | `tournaments_processed >= 1`; `results_updated >= 2`; `errors == []`. |
| E2E-04 | Экспорт PDF/XLSX/PNG | Каждый файл создан и имеет `size > 0`; при headless-ограничении PNG сценарий помечается skip с понятной причиной. |
| E2E-05 | Запись и фильтрация журнала | После 2 событий: `len(all_events)==2`, фильтр по `EXPORT_FILE` возвращает 1 запись; экспорт журнала создаёт txt-файл `size > 0`; в тексте нет `Traceback`. |

---

## 3. Критерий прохождения / блокирующий дефект

| Проверка | Критерий прохождения | Блокирующий дефект (стоп релиза) | Что делать дальше |
|---|---|---|---|
| Unit (`pytest -m unit`) | Все тесты зелёные | Любой fail по алгоритмам начисления/разрядов/рейтинга | Исправить логику, повторить unit и integration |
| Integration (`pytest -m integration`) | Все тесты зелёные | Любой fail в связке сервис+БД+файлы (импорт, пересчёт, экспорт, журнал) | Исправить сервис/миграции/форматы, повторить integration |
| Release smoke (`pytest -m release_smoke`) | Критический путь пройден; PNG допускает `skip` только для headless Qt | Fail в импорте, пересчёте, PDF/XLSX-экспорте, аудите, либо необъяснимый traceback | Блок релиза, фикс дефекта, полный повтор smoke |
| Traceback-контроль | В логах smoke-теста нет `Traceback` | Любой необработанный traceback | Блок релиза до устранения причины |

Правило выхода после прогона:
- Если есть хотя бы один блокирующий дефект — релиз не выпускать.
- Если блокирующих дефектов нет — переходить к шагам релизного чеклиста (`10_RELEASE_CHECKLIST.md`).

---

Конец документа.

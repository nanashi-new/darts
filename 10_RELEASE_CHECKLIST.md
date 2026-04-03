# 10 — Чек-лист релиза

Перед передачей приложения:

CI-пайплайн релизных проверок: [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

Фактический прогон зафиксирован: 2026-04-03 13:03 UTC, `work@3cf6269` (pre-squash SHA прогона; post-squash SHA не назначен), артефакт [`docs/artifacts/release-manual-scenarios-2026-04-03.log`](docs/artifacts/release-manual-scenarios-2026-04-03.log).

- [ ] Все тесты из `09_TEST_PLAN.md` пройдены (полный набор не закрыт в рамках этого прогона)
- [x] Заполнен отчёт ручного прогона по шаблону `docs/release_manual_run_template.md`
- [x] В отчёте есть ссылки на результаты для разделов import/recalc/export/merge/audit
- [x] `mypy app` завершился с `Success: no issues found`
- [x] dependency integrity check passed (`python -m pip check`)
- [x] Импорт реальных XLSX без ошибок
- [x] Экспорт PDF не обрезается
- [x] Экспорт Excel корректный
- [x] Экспорт изображения читаемый
- [x] Бэкап и восстановление базы работают
- [x] FAQ открывается из меню и загружается из `FAQ.txt`
- [x] Версия приложения отображается во вкладке «О программе»
- [ ] Приложение собрано в `.exe`
- [ ] Запуск на чистом ПК без Python

---

Релиз **не готов**: остаются незакрытые пункты по подтверждению Windows smoke, а также `.exe` + запуск на чистом Windows-профиле.

Правило процесса: PR/релиз **не закрывается**, пока не приложен заполненный отчёт ручного прогона и ссылки на результаты по обязательным пунктам import/recalc/export/merge/audit.

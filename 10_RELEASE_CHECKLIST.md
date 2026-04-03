# 10 — Чек-лист релиза

Перед передачей приложения:

CI-пайплайн релизных проверок: [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

Фактический прогон зафиксирован: 2026-04-03 11:18 UTC, `work@d130bf5` (pre-squash SHA прогона; post-squash SHA не назначен), артефакт [`docs/artifacts/release-check-smoke-2026-04-03.log`](docs/artifacts/release-check-smoke-2026-04-03.log).

- [ ] Все тесты из `09_TEST_PLAN.md` пройдены (в этом прогоне подтверждены только `mypy`, `pip check`, `release_smoke`; полный набор не закрыт)
- [x] Заполнен отчёт ручного прогона по шаблону `docs/release_manual_run_template.md`
- [x] В отчёте есть ссылки на результаты для разделов import/recalc/export/merge/audit
- [x] `mypy app` завершился с `Success: no issues found`
- [x] dependency integrity check passed (`python -m pip check`)
- [ ] Импорт реальных XLSX без ошибок
- [ ] Экспорт PDF не обрезается
- [ ] Экспорт Excel корректный
- [ ] Экспорт изображения читаемый
- [ ] Бэкап и восстановление базы работают
- [x] FAQ открывается из меню и загружается из `FAQ.txt`
- [x] Версия приложения отображается во вкладке «О программе»
- [ ] Приложение собрано в `.exe`
- [ ] Запуск на чистом ПК без Python

---

Релиз **не готов**: остаются незакрытые пункты чек-листа — ручные сценарии import/recalc/merge/audit, подтверждение Windows smoke, а также `.exe` + запуск на чистом ПК.

Правило процесса: PR/релиз **не закрывается**, пока не приложен заполненный отчёт ручного прогона и ссылки на результаты по обязательным пунктам import/recalc/export/merge/audit.

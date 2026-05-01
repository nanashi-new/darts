# Требования отчетов и карточки игрока

Статус: done  
Приоритет: P0  
Источник: `planning/reference/customer-requirements/2026-02-02-rating-system-requirements-approved.md`

## Цель

Сверить обязательные отчеты, экспорты и историю игрока с подтвержденными требованиями заказчика.

## Что меняем

- Проверить экспорт рейтинга и протокола турнира в `PDF` и `XLSX`.
- Проверить, что экспорт учитывает категорию/scope, дату и выбранный `N`.
- Проверить карточку игрока: турниры, очки, рейтинг, история лиг.
- Зафиксировать `CSV`, `Word` и `QR` как optional/future, если заказчик не делает их обязательными для v1.1.
- Проверить пакетный экспорт и release smoke на clean-profile.

## Что не трогаем

- Не делаем optional formats релизным блокером без отдельного решения.
- Не обещаем в FAQ или README форматы, которых еще нет.
- Не усложняем карточку игрока за пределы P0-сверки; развитие остается в `player-card-v2`.

## Тесты и проверки

- Targeted tests для export service.
- Targeted tests для player card/history.
- Ручной smoke: рейтинг -> PDF/XLSX, турнир -> PDF/XLSX, карточка игрока -> история.
- `pytest -q` после реализации.

## Критерии готовности

- Приоритетные форматы `PDF` и `XLSX` подтверждены.
- История игрока показывает данные, нужные для рабочего сценария заказчика.
- Optional formats явно отмечены как future, а не как забытая P0-дыра.

## Статус

- Done: добавлен clean-profile smoke для batch export в `PDF` и `XLSX` через свежий `DARTS_PROFILE_ROOT`.
- Done: batch export получил `export_all_to_profile(...)`, который пишет прямо в `profile/exports/<date>_run`, без вложенного `exports/exports`.
- Done: PDF export теперь гарантирует `QApplication` перед Qt PDF renderer, чтобы service/export smoke работал без поднятого UI.
- Done: targeted export gate `tests/test_export_features.py tests/test_release_smoke_max.py tests/test_clean_profile_export.py` проходит.
- Done: карточка игрока P0-сверена - показывает обзор, турниры, очки, текущие состояния рейтинга, историю лиг, заметки и тренировки.
- Done: карточка игрока получила scroll-friendly основу для плотного fullscreen/workspace режима.
- Done: пол и лиги в карточке, списке игроков, import-review и preview публикации показываются русскими подписями, технические коды остаются внутри данных.
- Done: targeted player/reporting UI gate `tests/test_ui_labels.py tests/test_player_card_dialog.py tests/test_players_view.py tests/test_import_apply_review_dialog.py` проходит.

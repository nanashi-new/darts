# 00 - Приоритет Выполнения

Этот файл - главный порядок разработки. Перед любой новой задачей сначала читать его, затем `planning/01_RULES.md`, затем связанный файл из `planning/tasks/`.

Если задачи нет здесь, она не считается основной рабочей задачей. Новые идеи сначала попадают в эту очередь или в отдельный task-файл.

## P0 - Сейчас

| Порядок | Задача | Статус | Task | Зависимости |
|---:|---|---|---|---|
| 1 | Очистить активное дерево и перенести старые планы в архив | done | [repo-cleanup.md](tasks/repo-cleanup.md) | система `planning/` |
| 2 | Стабилизировать текущую русификацию | done | [russian-ui-polish.md](tasks/russian-ui-polish.md) | merged in PR #65 |
| 3 | Переименовать продукт в «Дартс Лига» | done | [rename-to-darts-liga.md](tasks/rename-to-darts-liga.md) | текущая feature-ветка |
| 4 | Убрать старый бренд и старую классификацию из продукта и расчетов | done | [remove-old-brand-classification.md](tasks/remove-old-brand-classification.md) | текущая feature-ветка |
| 5 | Fullscreen workspace UI: запуск в большом рабочем режиме и оптимизация экранов под него | done | [fullscreen-workspace-ui.md](tasks/fullscreen-workspace-ui.md) | pytest green |
| 6 | UI polish: модалки, скроллы, кнопки, переполнение текста | done | [ui-modals-scroll-buttons.md](tasks/ui-modals-scroll-buttons.md) | fullscreen workspace UI |
| 7 | Требования рейтинга: очки, `N`, категории и взрослые зачеты | done | [rating-requirements-alignment.md](tasks/rating-requirements-alignment.md) | UI polish |
| 8 | Требования импорта: XLSX, aliases, ошибки и review-flow | done | [import-requirements-alignment.md](tasks/import-requirements-alignment.md) | UI polish |
| 9 | Требования турниров и лиг: manual adult, correction, archive/cancel/delete, переходы | done | [tournament-league-requirements-alignment.md](tasks/tournament-league-requirements-alignment.md) | rating/import alignment |
| 10 | Требования отчетов и карточки игрока: PDF/XLSX, история, optional formats | done | [reporting-player-requirements-alignment.md](tasks/reporting-player-requirements-alignment.md) | rating/import/tournament alignment |
| 11 | Финальная сверка продукта с подтвержденными требованиями заказчика | done | [customer-requirements-alignment.md](tasks/customer-requirements-alignment.md) | P0 задачи 7-10 |
| 12 | Небольшая автоматизация: подсказки, snapshots, restore points, preview переходов | done | [light-automation-v1.md](tasks/light-automation-v1.md) | P0 задачи 7-11 |
| 13 | Закрыть release readiness для v1.1 | done | [release-readiness.md](tasks/release-readiness.md) | P0 задачи 2-12; installer вынесен в P1 |

## P1 - Следующий слой удобства

| Порядок | Задача | Статус | Task | Зависимости |
|---:|---|---|---|---|
| 14 | Windows installer и релизная удобность | done | [windows-installer.md](tasks/windows-installer.md) | `DartsLiga*` артефакты |
| 15 | Главная как рабочий центр | done | [dashboard-command-center.md](tasks/dashboard-command-center.md) | v1.1 release-ready |
| 16 | Безопасность данных и backup/restore | done | [data-safety-and-backups.md](tasks/data-safety-and-backups.md) | release readiness |
| 17 | Автоматические сезонные переходы лиг “нижние 4 / верхние 4” | done | [league-season-transitions-v2.md](tasks/league-season-transitions-v2.md) | v1.1 release-ready |

## P2 - Дальнейшее развитие

| Порядок | Задача | Статус | Task | Зависимости |
|---:|---|---|---|---|
| 18 | Карточка игрока v2 | planned | [player-card-v2.md](tasks/player-card-v2.md) | dashboard/data safety |
| 19 | Полировка турнирного workflow | planned | [tournament-workflow-polish.md](tasks/tournament-workflow-polish.md) | fullscreen/UI polish |
| 20 | Расширение ежедневной работы: теги, вложения, кастомные поля, workspace | planned | [future-workspace-features.md](tasks/future-workspace-features.md) | player card v2 |

## P3 - Тренерский Слой

| Порядок | Задача | Статус | Task | Зависимости |
|---:|---|---|---|---|
| 21 | Coach workflow v1: follow-up, планы, контекст | planned | [coach-workflow-v1.md](tasks/coach-workflow-v1.md) | P2 daily workspace |

## P4 - Финальная Документация

| Порядок | Задача | Статус | Task | Зависимости |
|---:|---|---|---|---|
| 22 | Удобная FAQ-инструкция по работе в приложении | done | [faq-user-guide.md](tasks/faq-user-guide.md) | скроллируемый справочник и smoke-тест готовы |

## Правило Обновления

- После выполнения задачи обновить ее статус здесь.
- Если задача изменила состояние продукта, обновить `planning/03_CURRENT_STATE.md`.
- Если появились новые ограничения или правила, обновить `planning/01_RULES.md`.
- Старые документы из `planning/archive/` и release docs не становятся очередью задач без переноса сюда.

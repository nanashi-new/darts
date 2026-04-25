# 00 - Приоритет Выполнения

Этот файл - главный порядок разработки. Перед любой новой задачей сначала читать его, затем `planning/01_RULES.md`, затем связанный файл из `planning/tasks/`.

Если задачи нет здесь, она не считается основной рабочей задачей. Новые идеи сначала попадают в эту очередь или в отдельный task-файл.

## P0 - Сейчас

| Порядок | Задача | Статус | Task | Зависимости |
|---:|---|---|---|---|
| 1 | Очистить активное дерево и перенести старые планы в архив | done | [repo-cleanup.md](tasks/repo-cleanup.md) | система `planning/` |
| 2 | Стабилизировать текущую русификацию | done | [russian-ui-polish.md](tasks/russian-ui-polish.md) | merged in PR #65 |
| 3 | Переименовать продукт в «Дартс Лига» | done | [rename-to-darts-liga.md](tasks/rename-to-darts-liga.md) | ветка `feature/darts-liga-no-evsk` |
| 4 | Убрать старую классификацию из продукта и расчетов | done | [remove-evsk-ebck.md](tasks/remove-evsk-ebck.md) | ветка `feature/darts-liga-no-evsk` |
| 5 | Закрыть release readiness для v1.1 | planned | [release-readiness.md](tasks/release-readiness.md) | P0 задачи 2-4 |

## P1 - Следующий слой удобства

| Порядок | Задача | Статус | Task | Зависимости |
|---:|---|---|---|---|
| 6 | UI polish: модалки, скроллы, кнопки, переполнение текста | planned | [ui-modals-scroll-buttons.md](tasks/ui-modals-scroll-buttons.md) | P0 стабилизирован |
| 7 | Windows installer и релизная удобность | in progress | [windows-installer.md](tasks/windows-installer.md) | `DartsLiga*` артефакты |

## P2 - Дальнейшее развитие

| Порядок | Задача | Статус | Task | Зависимости |
|---:|---|---|---|---|
| 8 | Расширение ежедневной работы: теги, вложения, кастомные поля, workspace | planned | [future-workspace-features.md](tasks/future-workspace-features.md) | v1.1 release-ready |

## Правило Обновления

- После выполнения задачи обновить ее статус здесь.
- Если задача изменила состояние продукта, обновить `planning/03_CURRENT_STATE.md`.
- Если появились новые ограничения или правила, обновить `planning/01_RULES.md`.
- Старые документы из `planning/archive/` и release docs не становятся очередью задач без переноса сюда.

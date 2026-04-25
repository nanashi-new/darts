# Task: Переименовать продукт в «Дартс Лига»

## Цель

Убрать старое название из продукта и релизных артефактов. Новое пользовательское имя: «Дартс Лига».

## Что Меняем

- Заголовок главного окна.
- About screen.
- README и пользовательские docs.
- Installer script.
- PyInstaller specs.
- Build/release scripts.
- Release checklist.
- Логи старта и видимые сообщения, где упоминается старый бренд.

Технические имена артефактов:

- `DartsLiga.exe`
- `DartsLiga-release.zip`
- `DartsLiga-Setup.exe`
- `installer/DartsLiga.iss`

## Что Не Трогаем

- БД пользователя.
- Runtime profile paths, если они не показывают старый бренд пользователю.
- Бизнес-логику рейтинга.

## Тесты И Проверки

- `rg -n "Darts Rating EBCK|DartsRatingEBCK|EBCK|ЕВСК|EVSK"` после выполнения.
- Проверить главное окно и About.
- Проверить build scripts на новые имена артефактов.
- Проверить installer script на `DartsLiga`.

## Готово, Если

- Видимый продукт называется «Дартс Лига».
- Релизные артефакты называются `DartsLiga*`.
- Старый бренд не встречается в UI, README, release docs и scripts.
- Статус: выполнено в ветке `feature/darts-liga-no-evsk`.

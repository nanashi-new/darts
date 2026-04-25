# Task: Windows Installer И Релизная Удобность

## Цель

Сделать установку на Windows понятной для обычного пользователя.

## Что Меняем

- Поддерживать Inno Setup installer.
- Переименовать installer artifact после бренд-задачи в `DartsLiga-Setup.exe`.
- Оставить ZIP/exe fallback.
- Обновить русскую инструкцию установки.
- Проверить clean-profile запуск после установки.

## Что Не Трогаем

- Пользовательские данные при uninstall.
- Offline dependency policy без отдельной задачи.

## Тесты И Проверки

- `scripts\BUILD_RELEASE.bat`
- `scripts\SMOKE_TEST.bat`
- `scripts\PACK_RELEASE.bat`
- `scripts\BUILD_INSTALLER.bat`, если установлен Inno Setup 6.
- Ручной запуск из Start menu shortcut.

## Готово, Если

- Installer собирается.
- Installer UI русский.
- Установленное приложение стартует с чистым профилем.
- Uninstall удаляет программу, но не пользовательские данные.

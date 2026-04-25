# 14 - Установщик Windows

Active installer work is tracked in [`../planning/tasks/windows-installer.md`](../planning/tasks/windows-installer.md).
Use this document as user/release reference material.

## Назначение

Установщик нужен для обычного пользовательского сценария: скачать один `.exe`, установить приложение в папку программ и запустить его через ярлык.

ZIP-сборка остается запасным вариантом для ручной доставки и проверки.

## Как собрать

1. Соберите однофайловое приложение:

```bat
scripts\BUILD_RELEASE.bat
```

2. Соберите установщик:

```bat
scripts\BUILD_INSTALLER.bat
```

Результат:

- `release\DartsLiga-Setup.exe`

## Требования

- Windows
- Inno Setup 6
- готовый файл `dist\DartsLiga.exe`

Скрипт ищет `ISCC.exe` в стандартных папках установки Inno Setup и в `PATH`.

## Проверка

Перед публикацией релиза:

- установить приложение через `release\DartsLiga-Setup.exe`
- запустить приложение из меню Пуск или ярлыка
- проверить первый запуск на чистом профиле
- проверить экспорт PDF/XLSX/PNG
- проверить, что интерфейс отображается на русском

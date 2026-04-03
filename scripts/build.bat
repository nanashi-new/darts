@echo off
setlocal

cd /d %~dp0\..

echo [1/5] Установка зависимостей проекта...
if not exist requirements-pinned.txt (
  echo Файл requirements-pinned.txt не найден. Для release/offline-сборки нужен pinned-список зависимостей.
  exit /b 1
)

if exist vendor\wheels (
  echo Найден локальный кэш wheel-пакетов: vendor\wheels
  python -m pip install --no-index --find-links vendor\wheels -r requirements-pinned.txt
) else (
  python -m pip install -r requirements-pinned.txt
)
if errorlevel 1 (
  echo Не удалось установить зависимости из requirements-pinned.txt.
  exit /b 1
)

echo [2/5] Проверка PyInstaller...
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
  echo PyInstaller не найден. Выполняется установка...
  if exist vendor\wheels (
    python -m pip install --no-index --find-links vendor\wheels pyinstaller==6.19.0
  ) else (
    python -m pip install pyinstaller
  )
  if errorlevel 1 (
    echo Не удалось установить PyInstaller.
    exit /b 1
  )
)

echo [3/5] Очистка предыдущей сборки...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [4/5] Сборка через PyInstaller...
python -m PyInstaller pyinstaller.spec
if errorlevel 1 (
  echo Сборка завершилась с ошибкой.
  exit /b 1
)

echo [5/5] Готово.
echo Итоговый файл: dist\DartsRatingEBCK\DartsRatingEBCK.exe
endlocal

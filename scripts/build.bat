@echo off
setlocal

cd /d %~dp0\..

echo [1/5] Установка зависимостей проекта...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo Не удалось установить зависимости из requirements.txt.
  exit /b 1
)

echo [2/5] Проверка PyInstaller...
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
  echo PyInstaller не найден. Выполняется установка...
  python -m pip install pyinstaller
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

@echo off
setlocal

cd /d %~dp0\..

echo [1/3] Очистка предыдущей сборки...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [2/3] Сборка через PyInstaller...
pyinstaller pyinstaller.spec
if errorlevel 1 (
  echo Сборка завершилась с ошибкой.
  exit /b 1
)

echo [3/3] Готово.
echo Итоговая папка: dist\DartsRatingEBCK
endlocal

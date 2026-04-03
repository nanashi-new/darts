@echo off
setlocal

cd /d %~dp0\..

if not exist vendor mkdir vendor
if not exist vendor\wheels mkdir vendor\wheels

echo [1/3] Скачивание runtime-зависимостей в vendor\wheels...
python -m pip download -r requirements-pinned.txt -d vendor\wheels
if errorlevel 1 (
  echo Не удалось скачать runtime-зависимости.
  exit /b 1
)

echo [2/3] Скачивание PyInstaller в vendor\wheels...
python -m pip download pyinstaller==6.19.0 -d vendor\wheels
if errorlevel 1 (
  echo Не удалось скачать PyInstaller.
  exit /b 1
)

echo [3/3] Готово. Оффлайн-пакеты сохранены в vendor\wheels
endlocal

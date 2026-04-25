@echo off
setlocal

cd /d %~dp0\..

set "WHEELS_DIR=vendor\wheels"
set "MANIFEST_FILE=%WHEELS_DIR%\manifest.json"
set "VALIDATE_SCRIPT=%TEMP%\validate_wheels_manifest_%RANDOM%.py"

echo [1/5] Установка зависимостей проекта...
if not exist requirements-pinned.txt (
  echo Файл requirements-pinned.txt не найден. Для release/offline-сборки нужен pinned-список зависимостей.
  exit /b 1
)

if exist "%WHEELS_DIR%" (
  echo Найден локальный кэш wheel-пакетов: %WHEELS_DIR%
  if not exist "%MANIFEST_FILE%" (
    echo Не найден manifest: %MANIFEST_FILE%
    exit /b 1
  )

  echo Проверка версий и хэшей wheel-пакетов...
  (
    echo import hashlib
    echo import json
    echo import pathlib
    echo import re
    echo import sys
    echo.
    echo req_file = pathlib.Path('requirements-pinned.txt')
    echo wheels_dir = pathlib.Path('vendor/wheels')
    echo manifest_path = wheels_dir / 'manifest.json'
    echo.
    echo def normalize(name: str^) -^> str:
    echo     return re.sub(r'[-_.]+', '-', name^).lower(^)
    echo.
    echo def parse_requirements(path: pathlib.Path^):
    echo     requirements = {}
    echo     for raw in path.read_text(encoding='utf-8'^).splitlines(^):
    echo         line = raw.strip(^)
    echo         if not line or line.startswith('#'^):
    echo             continue
    echo         if '==' not in line:
    echo             raise SystemExit(f'Только фиксированные версии поддерживаются: {line}'^)
    echo         package, version = [part.strip(^) for part in line.split('==', 1^)]
    echo         requirements[normalize(package^)] = {'package': package, 'version': version}
    echo     return requirements
    echo.
    echo requirements = parse_requirements(req_file^)
    echo manifest = json.loads(manifest_path.read_text(encoding='utf-8'^)^)
    echo entries = manifest.get('entries', []^)
    echo manifest_map = {normalize(item['package']^): item for item in entries}
    echo.
    echo errors = []
    echo for normalized_name, expected in requirements.items(^):
    echo     if normalized_name not in manifest_map:
    echo         errors.append(f"В manifest нет записи для {expected['package']}=={expected['version']}")
    echo         continue
    echo     item = manifest_map[normalized_name]
    echo     if item.get('version'^) != expected['version']:
    echo         errors.append(
    echo             f"Версия {expected['package']} не совпадает: expected {expected['version']} got {item.get('version')}"
    echo         )
    echo         continue
    echo     wheel_path = wheels_dir / item['filename']
    echo     if not wheel_path.exists(^):
    echo         errors.append(f"Отсутствует wheel-файл: {wheel_path}")
    echo         continue
    echo     actual_hash = hashlib.sha256(wheel_path.read_bytes(^)^).hexdigest(^)
    echo     if actual_hash != item.get('sha256'^):
    echo         errors.append(
    echo             f"Хэш не совпадает для {item['filename']}: expected {item.get('sha256')} got {actual_hash}"
    echo         )
    echo.
    echo if errors:
    echo     for error in errors:
    echo         print(error^)
    echo     sys.exit(1^)
    echo.
    echo print('Manifest и wheel-кэш успешно прошли проверку.'^)
  ) > "%VALIDATE_SCRIPT%"

  python "%VALIDATE_SCRIPT%"
  if errorlevel 1 (
    del /q "%VALIDATE_SCRIPT%" >nul 2>&1
    echo Проверка локального wheel-кэша завершилась с ошибкой.
    exit /b 1
  )
  del /q "%VALIDATE_SCRIPT%" >nul 2>&1

  python -m pip install --no-index --find-links "%WHEELS_DIR%" -r requirements-pinned.txt
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
  if exist "%WHEELS_DIR%" (
    python -m pip install --no-index --find-links "%WHEELS_DIR%" pyinstaller==6.19.0
  ) else (
    python -m pip install pyinstaller==6.19.0
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
echo Итоговый файл: dist\DartsLiga\DartsLiga.exe
endlocal

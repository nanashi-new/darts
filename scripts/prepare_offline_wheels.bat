@echo off
setlocal

cd /d %~dp0\..

set "WHEELS_DIR=vendor\wheels"
set "MANIFEST_FILE=%WHEELS_DIR%\manifest.json"
set "MANIFEST_SCRIPT=%TEMP%\generate_wheels_manifest_%RANDOM%.py"

if not exist vendor mkdir vendor
if not exist "%WHEELS_DIR%" mkdir "%WHEELS_DIR%"

echo [1/3] Очистка старых wheel-пакетов...
if exist "%WHEELS_DIR%\*.whl" del /q "%WHEELS_DIR%\*.whl"
if exist "%MANIFEST_FILE%" del /q "%MANIFEST_FILE%"

echo [2/3] Скачивание зависимостей из requirements-pinned.txt...
if not exist requirements-pinned.txt (
  echo Файл requirements-pinned.txt не найден.
  exit /b 1
)

python -m pip download --only-binary=:all: -r requirements-pinned.txt -d "%WHEELS_DIR%"
if errorlevel 1 (
  echo Не удалось скачать зависимости из requirements-pinned.txt.
  exit /b 1
)

echo [3/3] Формирование manifest с именами/версиями/хэшами...
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
  echo requirements = []
  echo for raw in req_file.read_text(encoding='utf-8'^).splitlines(^):
  echo     line = raw.strip(^)
  echo     if not line or line.startswith('#'^):
  echo         continue
  echo     if '==' not in line:
  echo         raise SystemExit(f'Только фиксированные версии поддерживаются: {line}'^)
  echo     package, version = [part.strip(^) for part in line.split('==', 1^)]
  echo     requirements.append((package, version^)^)
  echo.
  echo wheel_files = sorted(wheels_dir.glob('*.whl'^)^)
  echo entries = []
  echo missing = []
  echo for package, version in requirements:
  echo     expected_name = normalize(package^)
  echo     matches = [wheel for wheel in wheel_files if normalize(wheel.name.split('-', 1^)[0]^)== expected_name]
  echo     if not matches:
  echo         missing.append(f'{package}=={version}'^)
  echo         continue
  echo     wheel_path = matches[0]
  echo     digest = hashlib.sha256(wheel_path.read_bytes(^)^).hexdigest(^)
  echo     entries.append({
  echo         'package': package,
  echo         'version': version,
  echo         'filename': wheel_path.name,
  echo         'sha256': digest,
  echo     }^)
  echo.
  echo if missing:
  echo     print('Не найдены wheel-файлы для:', ', '.join(missing^)^)
  echo     sys.exit(1^)
  echo.
  echo manifest = {
  echo     'generated_from': str(req_file^),
  echo     'entries': entries,
  echo }
  echo manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2^) + '\n', encoding='utf-8'^)
  echo print(f'Manifest сохранен: {manifest_path}'^)
) > "%MANIFEST_SCRIPT%"

python "%MANIFEST_SCRIPT%"
if errorlevel 1 (
  del /q "%MANIFEST_SCRIPT%" >nul 2>&1
  echo Не удалось сформировать manifest.
  exit /b 1
)

del /q "%MANIFEST_SCRIPT%" >nul 2>&1

echo Готово. Оффлайн-пакеты и manifest сохранены в %WHEELS_DIR%
endlocal

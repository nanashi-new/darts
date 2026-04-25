@echo off
setlocal

cd /d %~dp0\..

set "WHEELS_DIR=vendor\wheels"
set "MANIFEST_FILE=%WHEELS_DIR%\manifest.json"
set "ARTIFACT=dist\DartsLiga.exe"

if not exist requirements-pinned.txt (
  echo requirements-pinned.txt not found.
  exit /b 1
)

if exist "%WHEELS_DIR%" (
  if not exist "%MANIFEST_FILE%" (
    echo Offline manifest not found: %MANIFEST_FILE%
    exit /b 1
  )

  python scripts\validate_wheels_manifest.py
  if errorlevel 1 (
    echo Offline wheel validation failed.
    exit /b 1
  )

  python -m pip install --no-index --find-links "%WHEELS_DIR%" -r requirements-pinned.txt
) else (
  python -m pip install -r requirements-pinned.txt
)
if errorlevel 1 (
  echo Failed to install requirements-pinned.txt dependencies.
  exit /b 1
)

python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
  if exist "%WHEELS_DIR%" (
    python -m pip install --no-index --find-links "%WHEELS_DIR%" pyinstaller==6.19.0
  ) else (
    python -m pip install pyinstaller==6.19.0
  )
  if errorlevel 1 (
    echo Failed to install PyInstaller.
    exit /b 1
  )
)

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

python scripts\generate_build_info.py
if errorlevel 1 (
  echo Failed to generate build metadata.
  exit /b 1
)

python -m PyInstaller pyinstaller.release.spec --noconfirm
if errorlevel 1 (
  echo Release build failed.
  exit /b 1
)

if not exist "%ARTIFACT%" (
  echo Release artifact not found: %ARTIFACT%
  exit /b 1
)

echo Release artifact: %ARTIFACT%
endlocal

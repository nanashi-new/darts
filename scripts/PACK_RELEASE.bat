@echo off
setlocal

cd /d %~dp0\..

if not exist dist\DartsLiga.exe (
  echo Release exe not found. Run scripts\BUILD_RELEASE.bat first.
  exit /b 1
)

if not exist release mkdir release
set "ZIP_PATH=release\DartsLiga-release.zip"
if exist "%ZIP_PATH%" del /q "%ZIP_PATH%"

powershell -NoProfile -Command "Compress-Archive -Path 'dist\DartsLiga.exe','docs\11_RELEASE_TEST_RUN.md','10_RELEASE_CHECKLIST.md' -DestinationPath '%ZIP_PATH%' -Force"
if errorlevel 1 exit /b 1

echo Packed release: %ZIP_PATH%
endlocal

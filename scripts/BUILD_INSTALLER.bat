@echo off
setlocal

cd /d %~dp0\..

set "ARTIFACT=dist\DartsLiga.exe"
set "SCRIPT=installer\DartsLiga.iss"

if not exist "%ARTIFACT%" (
  echo Release exe not found. Run scripts\BUILD_RELEASE.bat first.
  exit /b 1
)

if not exist "%SCRIPT%" (
  echo Installer script not found: %SCRIPT%
  exit /b 1
)

set "ISCC_EXE="
for %%P in (
  "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
  "%ProgramFiles%\Inno Setup 6\ISCC.exe"
) do (
  if exist %%~P set "ISCC_EXE=%%~P"
)

if "%ISCC_EXE%"=="" (
  where ISCC.exe >nul 2>&1
  if errorlevel 1 (
    echo Inno Setup compiler not found. Install Inno Setup 6 or add ISCC.exe to PATH.
    exit /b 1
  )
  set "ISCC_EXE=ISCC.exe"
)

if not exist release mkdir release
"%ISCC_EXE%" "%SCRIPT%"
if errorlevel 1 (
  echo Installer build failed.
  exit /b 1
)

echo Installer artifact: release\DartsLiga-Setup.exe
endlocal

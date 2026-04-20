@echo off
setlocal

cd /d %~dp0\..

pytest -q tests\test_runtime_diagnostics.py tests\test_release_smoke_max.py tests\test_ui_tabs_content_smoke.py
if errorlevel 1 exit /b 1

if not exist dist\DartsRatingEBCK.exe (
  echo Release exe not found. Run scripts\BUILD_RELEASE.bat first.
  exit /b 1
)

set "PROFILE_ROOT=%TEMP%\DartsSmoke_%RANDOM%%RANDOM%"
set "ARTIFACT=%CD%\dist\DartsRatingEBCK.exe"

powershell -NoProfile -Command ^
  "$ErrorActionPreference = 'Stop'; " ^
  "$profileRoot = [System.IO.Path]::GetFullPath('%PROFILE_ROOT%'); " ^
  "$artifact = [System.IO.Path]::GetFullPath('%ARTIFACT%'); " ^
  "$env:DARTS_PROFILE_ROOT = $profileRoot; " ^
  "function Invoke-SmokeRun { " ^
  "  $p = Start-Process -FilePath $artifact -PassThru; " ^
  "  Start-Sleep -Seconds 5; " ^
  "  if (-not $p.HasExited) { Stop-Process -Id $p.Id; Start-Sleep -Seconds 1; return 0 } " ^
  "  return $p.ExitCode " ^
  "} " ^
  "$first = Invoke-SmokeRun; if ($first -ne 0) { throw 'First packaged run failed.' } " ^
  "$required = @('app.db','settings.json','norms.xlsx','logs\startup.log'); " ^
  "foreach ($entry in $required) { if (-not (Test-Path (Join-Path $profileRoot $entry))) { throw ('Missing required profile artifact: ' + $entry) } } " ^
  "$second = Invoke-SmokeRun; if ($second -ne 0) { throw 'Second packaged run failed.' } " ^
  "Write-Host ('Smoke profile root: ' + $profileRoot);"
if errorlevel 1 exit /b 1

echo Packaged smoke succeeded for profile: %PROFILE_ROOT%
endlocal

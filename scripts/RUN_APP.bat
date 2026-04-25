@echo off
setlocal

cd /d %~dp0\..

if exist dist\DartsLiga.exe (
  start "" /wait dist\DartsLiga.exe
  exit /b %errorlevel%
)

python -m app
exit /b %errorlevel%

@echo off
setlocal

cd /d %~dp0\..

if exist dist\DartsRatingEBCK.exe (
  start "" /wait dist\DartsRatingEBCK.exe
  exit /b %errorlevel%
)

python -m app
exit /b %errorlevel%

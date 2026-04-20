@echo off
setlocal
cd /d %~dp0
call prepare_offline_wheels.bat
endlocal

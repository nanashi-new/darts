@echo off
setlocal

cd /d %~dp0\..

python -c "from app.runtime_paths import get_runtime_paths; print(get_runtime_paths().profile_root)"
set /p CONFIRM=Type YES to remove the current profile root: 
if /I not "%CONFIRM%"=="YES" exit /b 1

for /f "usebackq delims=" %%P in (`python -c "from app.runtime_paths import get_runtime_paths; print(get_runtime_paths().profile_root)"`) do set "PROFILE_ROOT=%%P"
if exist "%PROFILE_ROOT%" rmdir /s /q "%PROFILE_ROOT%"
echo Removed profile root: %PROFILE_ROOT%
endlocal

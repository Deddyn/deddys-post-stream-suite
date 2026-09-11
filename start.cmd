@echo off
cd /d "%~dp0"
if exist "DeddysPostStreamSuite.exe" (
  start "" "DeddysPostStreamSuite.exe"
  exit /b
)
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -m vodstamp
) else (
  python -m vodstamp
)
if errorlevel 1 pause

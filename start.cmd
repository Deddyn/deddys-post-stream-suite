@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 -m vodstamp
) else (
  where python >nul 2>nul
  if not errorlevel 1 (
    python -m vodstamp
  ) else (
    if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
      "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m vodstamp
    ) else (
      echo Python non trovato. Consulta README.md per il setup.
      pause
      exit /b 1
    )
  )
)
if errorlevel 1 pause

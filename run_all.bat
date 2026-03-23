@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_all.ps1"
if errorlevel 1 (
  echo.
  echo NASSAV failed to start. Check the error messages above.
  pause
)
endlocal

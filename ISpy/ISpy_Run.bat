@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title LookupTool v7
cd /d %~dp0

REM === Auto-install requirements (if any) ===
set REQS=requirements.txt
if exist "%REQS%" (
  for /f "usebackq delims=" %%L in ("%REQS%") do (
    echo %%L | findstr /R "^[ ]*#">nul || (
      echo %%L | findstr /R "^[ ]*$">nul || set NONEMPTY=1
    )
  )
  if defined NONEMPTY (
    echo [Setup] Installing Python packages from %REQS% ...
    where py >nul 2>nul
    if %errorlevel%==0 (
      py -3 -m pip install -r "%REQS%"
    ) else (
      python -m pip install -r "%REQS%"
    )
  ) else (
    echo [Setup] No third-party packages needed.
  )
) else (
  echo [Setup] No requirements.txt found.
)


if not exist logs mkdir logs

set LOG=logs\run.log
echo ==== Run started: %date% %time% ==== > "%LOG%"
echo [Info] Launching bootstrap.py >> "%LOG%"

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -X faulthandler app\bootstrap.py >> "%LOG%" 2>&1
  set EXITCODE=%ERRORLEVEL%
) else (
  python -X faulthandler app\bootstrap.py >> "%LOG%" 2>&1
  set EXITCODE=%ERRORLEVEL%
)

if not "%EXITCODE%"=="0" (
  echo.
  echo The app failed to start. Showing log (logs\run.log) ...
  echo -------------------------------------------------------
  type "%LOG%"
  echo -------------------------------------------------------
  echo.
  echo Press any key to close this window...
  pause >nul
  exit /b %EXITCODE%
)

REM Normal exit path
exit /b 0

@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title LookupTool v7 (Debug)
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


echo === Debug launcher ===
where py >nul 2>nul
if %errorlevel%==0 (
  echo Using: py -3 -X dev -X faulthandler app\bootstrap.py
  py -3 -X dev -X faulthandler app\bootstrap.py
) else (
  echo Using: python -X dev -X faulthandler app\bootstrap.py
  python -X dev -X faulthandler app\bootstrap.py
)
echo.
echo (Window will stay open. Press any key to close.)
pause >nul

@echo off
title AI Job Hunter Pro - Live English CS HR Chat Responder
cd /d "%~dp0"

echo ==========================================================
echo [AI Job Hunter Pro] Live English CS HR Chat Responder
echo ==========================================================
echo.

echo [1/2] Cleaning up previous processes and stale locks...
powershell -Command "Get-Process -Name chrome, chromedriver -ErrorAction SilentlyContinue | Stop-Process -Force" >nul 2>&1
if exist "C:\chrome_debug_profile\Singleton*" del /f /q "C:\chrome_debug_profile\Singleton*" >nul 2>&1
if exist "C:\chrome_debug_profile\lockfile" del /f /q "C:\chrome_debug_profile\lockfile" >nul 2>&1

echo [2/2] Launching Native Persistent GUI Engine...
echo.

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0run_live_chat_responder.py"
) else (
    python "%~dp0run_live_chat_responder.py"
)

echo.
echo ==========================================================
pause

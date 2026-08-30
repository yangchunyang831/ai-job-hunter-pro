@echo off
title AI Job Hunter Pro - Live English CS HR Chat Responder
cd /d "%~dp0"

echo ==========================================================
echo [AI Job Hunter Pro] Live English CS HR Chat Responder
echo ==========================================================
echo.

echo [1/2] Cleaning up previous processes and stale locks...
taskkill /F /IM chrome.exe >nul 2>&1
timeout /t 1 /nobreak >nul
del /f /q "C:\chrome_debug_profile\Singleton*" >nul 2>&1
del /f /q "C:\chrome_debug_profile\lockfile" >nul 2>&1

echo [2/2] Starting Native Persistent GUI Engine...
echo.

if exist ".\.venv\Scripts\python.exe" (
    ".\.venv\Scripts\python.exe" run_live_chat_responder.py
) else (
    python run_live_chat_responder.py
)

echo.
echo ==========================================================
echo Process finished.
echo ==========================================================
pause

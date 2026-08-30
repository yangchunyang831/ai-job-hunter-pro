@echo off
title AI Job Hunter Pro - Live English CS HR Chat Responder
cd /d "%~dp0"

echo ==========================================================
echo [AI Job Hunter Pro] Live English CS HR Chat Responder
echo ==========================================================
echo.
echo [1/2] Checking Chrome status...
tasklist /FI "IMAGENAME eq chrome.exe" 2>NUL | find /I /N "chrome.exe">NUL
if "%ERRORLEVEL%"=="1" (
    echo Starting Chrome with debugging port...
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chrome_debug_profile" --no-first-run --no-default-browser-check "https://www.zhipin.com/web/geek/chat"
    timeout /t 4 /nobreak >nul
)

echo [2/2] Starting intelligent multi-turn HR responder...
echo.

if exist ".\.venv\Scripts\python.exe" (
    ".\.venv\Scripts\python.exe" run_live_chat_responder.py
) else (
    python run_live_chat_responder.py
)

pause

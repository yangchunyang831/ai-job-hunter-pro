@echo off
title AI Job Hunter Pro - Live English CS HR Chat Responder
cd /d "%~dp0"

echo ==========================================================
echo [AI Job Hunter Pro] Live English CS HR Chat Responder
echo ==========================================================
echo.

echo [1/3] Ensuring clean debugging environment and clearing locks...
taskkill /F /IM chrome.exe >nul 2>&1
timeout /t 1 /nobreak >nul
del /f /q "C:\chrome_debug_profile\Singleton*" >nul 2>&1
del /f /q "C:\chrome_debug_profile\lockfile" >nul 2>&1

echo [2/3] Launching Persistent Stealth Chrome...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chrome_debug_profile" --disable-blink-features=AutomationControlled --disable-infobars --no-first-run --no-default-browser-check "https://www.zhipin.com/web/geek/chat"

timeout /t 4 /nobreak >nul

echo [3/3] Starting intelligent multi-turn HR responder with Watchdog...
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

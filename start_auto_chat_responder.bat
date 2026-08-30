@echo off
title AI Job Hunter Pro - Live English CS HR Chat Responder
cd /d "%~dp0"

echo ==========================================================
echo [AI Job Hunter Pro] Live English CS HR Chat Responder
echo ==========================================================
echo.

echo [1/2] Launching Chrome directly to BOSS Chat...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chrome_debug_profile" --no-first-run --no-default-browser-check "https://www.zhipin.com/web/geek/chat"

timeout /t 3 /nobreak >nul

echo [2/2] Starting intelligent multi-turn HR responder...
echo.

if exist ".\.venv\Scripts\python.exe" (
    ".\.venv\Scripts\python.exe" run_live_chat_responder.py
) else (
    python run_live_chat_responder.py
)

echo.
echo Process finished.
pause

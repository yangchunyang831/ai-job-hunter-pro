@echo off
title AI Job Hunter Pro
cd /d "%~dp0"

echo ==========================================================
echo [AI Job Hunter Pro] Live Real-World HR Communication
echo ==========================================================
echo.
echo Starting Chrome browser...
taskkill /f /im chrome.exe >nul 2>&1
echo.

if exist ".\.venv\Scripts\python.exe" (
    ".\.venv\Scripts\python.exe" run_single_live_chat.py
) else (
    python run_single_live_chat.py
)

pause

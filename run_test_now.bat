@echo off
title AI Job Hunter Pro - Live HR Chat Room Runner
cd /d "%~dp0"

echo ==========================================================
echo [AI Job Hunter Pro] Live Real-World HR Chat Room Runner
echo ==========================================================
echo.
echo Cleaning orphan processes...
taskkill /f /im chrome.exe >nul 2>&1
echo.

if exist ".\.venv\Scripts\python.exe" (
    ".\.venv\Scripts\python.exe" run_live_chat_conversation.py
) else (
    python run_live_chat_conversation.py
)

pause

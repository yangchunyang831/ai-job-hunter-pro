@echo off
title AI Job Hunter Pro - Live HR Communication
cd /d "%~dp0"

echo ==========================================================
echo [AI Job Hunter Pro] Live Real-World HR Communication
echo ==========================================================
echo.
echo Connecting to live Chrome window and initiating communication...
echo.

if exist ".\.venv\Scripts\python.exe" (
    ".\.venv\Scripts\python.exe" run_single_live_chat.py
) else (
    python run_single_live_chat.py
)

pause

@echo off
title AI Job Hunter - Chrome Debug Launcher
cd /d "%~dp0"

if exist ".\.venv\Scripts\python.exe" (
    ".\.venv\Scripts\python.exe" main.py start-chrome
) else (
    python main.py start-chrome
)

if %errorlevel% neq 0 (
    echo.
    echo [Error] Failed to start Chrome debugger.
    pause
)

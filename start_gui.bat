@echo off
title AI Job Hunter Pro - GUI Dashboard
cd /d "%~dp0"

echo Starting AI Job Hunter Pro Web Dashboard...

if exist ".\.venv\Scripts\python.exe" (
    ".\.venv\Scripts\python.exe" main.py gui
) else (
    python main.py gui
)

if %errorlevel% neq 0 (
    echo.
    echo [Error] Failed to start GUI Dashboard.
    pause
)

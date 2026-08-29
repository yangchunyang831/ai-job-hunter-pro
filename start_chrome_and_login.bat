@echo off
title AI Job Hunter Pro - Chrome Launcher
cd /d "%~dp0"

if exist ".\.venv\Scripts\python.exe" (
    ".\.venv\Scripts\python.exe" scripts\launch_chrome.py
) else (
    python scripts\launch_chrome.py
)

pause

@echo off
title AI Job Hunter Pro - Live Battle Runner
cd /d "%~dp0"

echo ==========================================================
echo [AI Job Hunter Pro] Live High-Risk Adversarial Test Runner
echo ==========================================================
echo.
echo Cleaning orphan processes...
taskkill /f /im chrome.exe >nul 2>&1
echo.

if exist ".\.venv\Scripts\python.exe" (
    ".\.venv\Scripts\python.exe" run_single_live_chat.py
) else (
    python run_single_live_chat.py
)

pause

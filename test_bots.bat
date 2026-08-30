@echo off
title AI Job Hunter Pro - WeChat and Feishu Bot Test Suite
cd /d "%~dp0"

echo ==========================================================
echo [AI Job Hunter Pro] WeChat and Feishu Bot Test Suite
echo ==========================================================
echo.

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0scripts\test_bots.py"
) else (
    python "%~dp0scripts\test_bots.py"
)

echo.
echo ==========================================================
pause

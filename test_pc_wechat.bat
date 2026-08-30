@echo off
title AI Job Hunter Pro - PC WeChat Direct Connection
cd /d "%~dp0"

echo ==========================================================
echo [AI Job Hunter Pro] Testing Native PC WeChat Direct Link...
echo ==========================================================
echo.

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0scripts\test_pc_wechat.py"
) else (
    python "%~dp0scripts\test_pc_wechat.py"
)

echo.
echo ==========================================================
pause

@echo off
title AI Job Hunter Pro - Send WeChat Message
cd /d "%~dp0"

echo ==========================================================
echo [AI Job Hunter Pro] Sending WeChat Message to Contact Yang Chun...
echo ==========================================================
echo.

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0scripts\test_wechat_send_direct.py"
) else (
    python "%~dp0scripts\test_wechat_send_direct.py"
)

echo.
echo ==========================================================
pause

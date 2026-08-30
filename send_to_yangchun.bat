@echo off
chcp 65001 >nul
title AI Job Hunter Pro - Send Test Message to Yang Chun on WeChat

echo ==========================================================
echo [AI Job Hunter Pro] Sending WeChat Message to Contact "杨春"...
echo ==========================================================
echo.

if exist "d:\招聘\.venv\Scripts\python.exe" (
    "d:\招聘\.venv\Scripts\python.exe" "d:\招聘\scripts\send_to_yangchun.py"
) else (
    python "d:\招聘\scripts\send_to_yangchun.py"
)

echo.
echo ==========================================================
pause

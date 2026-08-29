@echo off
title AI Job Hunter Pro - Live Battle Runner
cd /d "%~dp0"

echo ==========================================================
echo [AI Job Hunter Pro] BOSS 直聘实战高危目标自动筛选与沟通
echo ==========================================================
echo.
echo 正在清理残留进程并启动可视化 Chrome...
taskkill /f /im chrome.exe >nul 2>&1
echo.

if exist ".\.venv\Scripts\python.exe" (
    ".\.venv\Scripts\python.exe" run_single_live_chat.py
) else (
    python run_single_live_chat.py
)

pause

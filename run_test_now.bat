@echo off
chcp 65001 >nul
title BOSS 直聘高危实战单次全流程沟通测试
cd /d "%~dp0"

echo ==========================================================
echo 🎯 BOSS 直聘高危企业实战单次沟通测试（严格排除湖南与怀化）
echo ==========================================================
echo.
echo 正在清理残留进程并启动有头 Chrome 浏览器...
taskkill /f /im chrome.exe >nul 2>&1
echo.

if exist ".\.venv\Scripts\python.exe" (
    ".\.venv\Scripts\python.exe" run_single_live_chat.py
) else (
    python run_single_live_chat.py
)

pause

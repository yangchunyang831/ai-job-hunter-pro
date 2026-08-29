@echo off
title BOSS 直聘高危实战单次全流程沟通测试
cd /d "%~dp0"

echo ==========================================================
echo 🎯 BOSS 直聘高危企业实战单次沟通测试（严格排除湖南与怀化）
echo ==========================================================
echo.
echo 正在启动有头 Chrome 浏览器并在前台执行沟通...
echo 实时日志将同步写入: logs\live_battle.log
echo.

if exist ".\.venv\Scripts\python.exe" (
    ".\.venv\Scripts\python.exe" run_single_live_chat.py
) else (
    python run_single_live_chat.py
)

pause

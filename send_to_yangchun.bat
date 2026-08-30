@echo off
chcp 65001 >nul
title AI Job Hunter Pro - Send Test Message to Yang Chun on WeChat

echo ==========================================================
echo [AI Job Hunter Pro] Sending WeChat Message to Contact Yang Chun...
echo ==========================================================
echo.

"d:\ÕÐÆ¸\.venv\Scripts\python.exe" "d:\ÕÐÆ¸\scripts\test_wechat_send_direct.py"

echo.
echo ==========================================================
pause

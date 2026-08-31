@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================================
echo 🤖 正在执行【文件传输助手】全自动模拟代聊测试...
echo ==========================================================
echo 提示: 请确保电脑微信处于登录状态
echo.

".venv\Scripts\python.exe" scripts\send_to_filehelper.py

echo.
pause

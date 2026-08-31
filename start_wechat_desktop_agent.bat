@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
title WeChat Desktop Live AI Auto-Responder
cd /d "%~dp0"

echo ==========================================================
echo [1/2] 确保本地大模型中转站正在运行 (Port 3000)...
echo ==========================================================
start /min "" "E:\NewAPI\new-api.exe" --port 3000

echo.
echo ==========================================================
echo [2/2] 启动桌面微信 AI 高情商自动代聊助手...
echo ==========================================================
echo 💡 请确保电脑微信窗口处于打开状态！
echo 🤖 人设已锁定：杨春（真诚孝顺、懂事、随时到岗）
echo.

".venv\Scripts\python.exe" run_wechat_desktop_agent.py

pause

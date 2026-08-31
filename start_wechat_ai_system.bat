@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
title WeChat AI Auto-Responder Hub (Akasha + AstrBot + NewAPI)
cd /d "%~dp0"

echo ==========================================================
echo [1/3] 启动本地大模型中转站 NewAPI (Port 3000)...
echo ==========================================================
start /min "" "E:\NewAPI\new-api.exe" --port 3000

echo.
echo ==========================================================
echo [2/3] 启动 AstrBot 智能中枢 (Port 6185 & OneBot 11229)...
echo ==========================================================
start /min "" "D:\AstrBot\.venv\Scripts\python.exe" "D:\AstrBot\main.py"

echo.
echo ==========================================================
echo [3/3] 启动 Akasha-WeChat 桥接服务 (Port 8766)...
echo ==========================================================
echo.
echo 🌐 微信桥接控制面板:   http://127.0.0.1:8766
echo 🤖 AstrBot 智能中枢:    http://127.0.0.1:6185
echo 🏢 本地大模型中转站:    http://127.0.0.1:3000
echo.
echo 💡 请确保 WeFlow 客户端正在运行并监听 5031 端口！
echo.

cd /d "D:\Akasha-WeChat\wechat-weflow-bridge-ob11"
"d:\招聘\.venv\Scripts\python.exe" main.py

pause

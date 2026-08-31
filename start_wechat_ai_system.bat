@echo off
chcp 65001 >nul
title WeChat AI Auto-Reply Unified System
cd /d "%~dp0"

echo ==========================================================
echo [1/4] 启动本地大模型中转站 (Port 3000)...
echo ==========================================================
start /min "NewAPI" "E:\NewAPI\new-api.exe" --port 3000

echo.
echo ==========================================================
echo [2/4] 启动 AstrBot 智能对话中枢 (Port 6185 / 11229)...
echo ==========================================================
start /min "AstrBot" "D:\AstrBot\.venv\Scripts\python.exe" "D:\AstrBot\main.py"

echo.
echo ==========================================================
echo [3/4] 启动 WeFlow 消息客户端 (D:\Tencent\Weixin\WeFlow)...
echo ==========================================================
start "" "D:\Tencent\Weixin\WeFlow\WeFlow.exe"

echo.
echo ==========================================================
echo [4/4] 启动 Akasha-WeChat 微信自动化桥接器...
echo ==========================================================
cd /d "D:\Tencent\Weixin\Akasha-WeChat\wechat-weflow-bridge-ob11"
"D:\招聘\.venv\Scripts\python.exe" main.py

pause

@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
title AstrBot Launcher - AI Job Hunter Pro Hub
cd /d "%~dp0"

echo ==========================================================
echo [1/2] Starting Local NewAPI Gateway (Port 3000)...
echo ==========================================================
start /min "" "E:\NewAPI\new-api.exe" --port 3000

echo.
echo ==========================================================
echo [2/2] Starting AstrBot Dashboard (Port 6185)...
echo ==========================================================
echo.
echo 🌐 AstrBot 控制面板 WebUI: http://127.0.0.1:6185
echo 🏢 本地 NewAPI 中转站:     http://127.0.0.1:3000
echo.

cd /d "D:\AstrBot"
"D:\AstrBot\.venv\Scripts\python.exe" main.py

pause

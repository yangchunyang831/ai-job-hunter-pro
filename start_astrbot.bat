@echo off
chcp 65001 >nul
title AstrBot Launcher - AI Job Hunter Pro Hub

echo ==========================================================
echo [AI Job Hunter Pro] Launching AstrBot from D:\AstrBot...
echo ==========================================================
echo.
echo 🌐 AstrBot 控制面板 WebUI: http://127.0.0.1:6185
echo.

if exist "D:\AstrBot\start_astrbot.bat" (
    call "D:\AstrBot\start_astrbot.bat"
) else (
    cd /d "D:\AstrBot"
    "D:\AstrBot\.venv\Scripts\python.exe" main.py
)

pause

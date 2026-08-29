@echo off
title Chrome Browser Real-Time Logs Viewer
cd /d "%~dp0"

echo ==========================================================
echo [AI Job Hunter Pro] Chrome 浏览器 DevTools / 网络日志监控
echo ==========================================================
echo.
echo 正在打开 Chrome 实时运行日志文件: logs\chrome_browser.log ...
echo.

if not exist "logs\chrome_browser.log" (
    echo [INFO] 日志文件尚未生成，将在浏览器启动后自动创建。 > logs\chrome_browser.log
)

powershell -Command "Get-Content -Path 'logs\chrome_browser.log' -Wait -Tail 30"

pause

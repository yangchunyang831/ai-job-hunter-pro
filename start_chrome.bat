@echo off
chcp 65001 >nul
echo ========================================================
echo   正在启动带调试端口 (9222) 的 Google Chrome 浏览器...
echo ========================================================
echo.
echo 1. 浏览器打开后，请在窗口中扫码登录 BOSS直聘 (https://www.zhipin.com)
echo 2. 登录成功后，即可在终端运行 Python 求职 Agent 脚本
echo.

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chrome_debug_profile" "https://www.zhipin.com"
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chrome_debug_profile" "https://www.zhipin.com"
) else (
    echo [错误] 未找到 Google Chrome 安装路径，请手动通过命令行启动。
    pause
    exit /b 1
)

echo Chrome 启动成功！端口 9222 已开放。

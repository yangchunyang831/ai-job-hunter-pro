@echo off
title AI Job Hunter Pro - Chrome Debug Launcher
cd /d "%~dp0"

echo ==========================================================
echo [AI Job Hunter Pro] 启动可直连调试的 Chrome 浏览器
echo ==========================================================
echo.
echo 正在为您启动 Chrome 并开启 CDP 自动化直连接口 (端口: 9222)...
echo.

start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chrome_debug_profile" "https://www.zhipin.com/web/geek/job?query=海外客服&city=101020100"

echo.
echo Chrome 窗口已成功在桌面打开！
echo.
echo 👉 请在该 Chrome 窗口中确认已处于登录状态（如需登录请微信扫码登录一次）；
echo 👉 随后直接双击运行 run_test_now.bat，系统将瞬间秒级直连并完成真机选岗与沟通！
echo.
pause

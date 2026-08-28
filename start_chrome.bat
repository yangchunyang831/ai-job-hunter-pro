@echo off
chcp 65001 >nul
title AI 求职 Agent - Chrome 调试环境启动器

echo ======================================================================
echo                AI Agent 专属 Chrome 调试浏览器启动器
echo ======================================================================
echo.

:: 1. 查找 Chrome 可执行文件路径
set "CHROME_PATH="
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
) else if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
)

if "%CHROME_PATH%"=="" (
    echo [❌ 错误] 未能自动找到 Google Chrome 安装路径！
    echo 请确认您已安装 Google Chrome 浏览器。
    echo.
    pause
    exit /b 1
)

echo [✓] 找到 Chrome 路径: "%CHROME_PATH%"

:: 2. 设置安全的数据存储目录 (避免 C 盘根目录权限受限)
set "DEBUG_PROFILE_DIR=%~dp0data\chrome_debug_profile"
if not exist "%DEBUG_PROFILE_DIR%" mkdir "%DEBUG_PROFILE_DIR%"
echo [✓] 调试缓存目录: "%DEBUG_PROFILE_DIR%"

:: 3. 启动 Chrome (开启 9222 调试端口与专属数据目录)
echo.
echo 正在启动 Chrome 浏览器并连接 9222 端口...
start "" "%CHROME_PATH%" --remote-debugging-port=9222 --user-data-dir="%DEBUG_PROFILE_DIR%" --no-first-run --no-default-browser-check "https://www.zhipin.com"

:: 4. 等待并检测端口
echo.
echo ======================================================================
echo  [✅ Chrome 已成功调起！]
echo.
echo  👉 请在弹出的 Chrome 窗口中进行以下操作：
echo     1. 使用手机端 BOSS直聘 App 扫码登录
echo     2. 保持该 Chrome 窗口不要关闭
echo.
echo  👉 登录完成后，请在新终端窗口运行求职 Agent：
echo     cd /d "%~dp0"
echo     .\.venv\Scripts\python main.py scan-only
echo ======================================================================
echo.
echo 按任意键可关闭此提示窗口 (浏览器窗口将继续保持运行)...
pause >nul

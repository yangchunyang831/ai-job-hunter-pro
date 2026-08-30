"""
Rewrite all batch files with relative %~dp0 paths to ensure 100% path resolution on any Windows system.
"""
from pathlib import Path

bat_files = {
    r"d:\招聘\send_to_yangchun.bat": """@echo off
title AI Job Hunter Pro - Send WeChat Message
cd /d "%~dp0"

echo ==========================================================
echo [AI Job Hunter Pro] Sending WeChat Message to Contact Yang Chun...
echo ==========================================================
echo.

if exist "%~dp0.venv\\Scripts\\python.exe" (
    "%~dp0.venv\\Scripts\\python.exe" "%~dp0scripts\\test_wechat_send_direct.py"
) else (
    python "%~dp0scripts\\test_wechat_send_direct.py"
)

echo.
echo ==========================================================
pause
""",
    r"d:\招聘\start_auto_chat_responder.bat": """@echo off
title AI Job Hunter Pro - Live English CS HR Chat Responder
cd /d "%~dp0"

echo ==========================================================
echo [AI Job Hunter Pro] Live English CS HR Chat Responder
echo ==========================================================
echo.

echo [1/2] Cleaning up previous processes and stale locks...
powershell -Command "Get-Process -Name chrome, chromedriver -ErrorAction SilentlyContinue | Stop-Process -Force" >nul 2>&1
if exist "C:\\chrome_debug_profile\\Singleton*" del /f /q "C:\\chrome_debug_profile\\Singleton*" >nul 2>&1
if exist "C:\\chrome_debug_profile\\lockfile" del /f /q "C:\\chrome_debug_profile\\lockfile" >nul 2>&1

echo [2/2] Launching Native Persistent GUI Engine...
echo.

if exist "%~dp0.venv\\Scripts\\python.exe" (
    "%~dp0.venv\\Scripts\\python.exe" "%~dp0run_live_chat_responder.py"
) else (
    python "%~dp0run_live_chat_responder.py"
)

echo.
echo ==========================================================
pause
""",
    r"d:\招聘\test_pc_wechat.bat": """@echo off
title AI Job Hunter Pro - PC WeChat Direct Connection
cd /d "%~dp0"

echo ==========================================================
echo [AI Job Hunter Pro] Testing Native PC WeChat Direct Link...
echo ==========================================================
echo.

if exist "%~dp0.venv\\Scripts\\python.exe" (
    "%~dp0.venv\\Scripts\\python.exe" "%~dp0scripts\\test_pc_wechat.py"
) else (
    python "%~dp0scripts\\test_pc_wechat.py"
)

echo.
echo ==========================================================
pause
""",
    r"d:\招聘\test_bots.bat": """@echo off
title AI Job Hunter Pro - WeChat and Feishu Bot Test Suite
cd /d "%~dp0"

echo ==========================================================
echo [AI Job Hunter Pro] WeChat and Feishu Bot Test Suite
echo ==========================================================
echo.

if exist "%~dp0.venv\\Scripts\\python.exe" (
    "%~dp0.venv\\Scripts\\python.exe" "%~dp0scripts\\test_bots.py"
) else (
    python "%~dp0scripts\\test_bots.py"
)

echo.
echo ==========================================================
pause
"""
}

for path, content in bat_files.items():
    with open(path, "wb") as f:
        f.write(content.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
    print(f"Updated {path} with bulletproof %~dp0 relative paths.")

"""
Script to write clean ANSI encoded .bat files for Windows cmd.exe.
"""
from pathlib import Path

bat_files = {
    r"d:\招聘\send_to_yangchun.bat": """@echo off
chcp 65001 >nul
title AI Job Hunter Pro - Send Test Message to Yang Chun on WeChat

echo ==========================================================
echo [AI Job Hunter Pro] Sending WeChat Message to Contact Yang Chun...
echo ==========================================================
echo.

"d:\\招聘\\.venv\\Scripts\\python.exe" "d:\\招聘\\scripts\\send_to_yangchun.py"

echo.
echo ==========================================================
pause
""",
    r"d:\招聘\test_pc_wechat.bat": """@echo off
chcp 65001 >nul
title AI Job Hunter Pro - PC WeChat Direct Connection

echo ==========================================================
echo [AI Job Hunter Pro] Testing Native PC WeChat Direct Link...
echo ==========================================================
echo.

"d:\\招聘\\.venv\\Scripts\\python.exe" "d:\\招聘\\scripts\\test_pc_wechat.py"

echo.
echo ==========================================================
pause
""",
    r"d:\招聘\test_bots.bat": """@echo off
chcp 65001 >nul
title AI Job Hunter Pro - WeChat and Feishu Bot Test Suite

echo ==========================================================
echo [AI Job Hunter Pro] WeChat and Feishu Bot Test Suite
echo ==========================================================
echo.

"d:\\招聘\\.venv\\Scripts\\python.exe" "d:\\招聘\\scripts\\test_bots.py"

echo.
echo ==========================================================
pause
"""
}

for path, content in bat_files.items():
    with open(path, "wb") as f:
        # Write with CRLF line endings in ANSI/GBK
        f.write(content.replace("\r\n", "\n").replace("\n", "\r\n").encode("gbk"))
    print(f"Updated {path} in clean GBK CRLF format.")

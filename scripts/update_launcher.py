"""
Update send_to_yangchun.bat to call test_wechat_send_direct.py.
"""
bat_content = """@echo off
chcp 65001 >nul
title AI Job Hunter Pro - Send Test Message to Yang Chun on WeChat

echo ==========================================================
echo [AI Job Hunter Pro] Sending WeChat Message to Contact Yang Chun...
echo ==========================================================
echo.

"d:\\招聘\\.venv\\Scripts\\python.exe" "d:\\招聘\\scripts\\test_wechat_send_direct.py"

echo.
echo ==========================================================
pause
"""

with open(r"d:\招聘\send_to_yangchun.bat", "wb") as f:
    f.write(bat_content.replace("\r\n", "\n").replace("\n", "\r\n").encode("gbk"))

print("send_to_yangchun.bat updated successfully in clean GBK CRLF format!")

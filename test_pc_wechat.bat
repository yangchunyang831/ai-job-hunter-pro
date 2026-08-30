@echo off
chcp 65001 >nul
title AI Job Hunter Pro - PC WeChat Direct Connection

echo ==========================================================
echo [AI Job Hunter Pro] Testing Native PC WeChat Direct Link (D:\Tencent\Weixin)
echo ==========================================================
echo.

if exist "d:\招聘\.venv\Scripts\python.exe" (
    "d:\招聘\.venv\Scripts\python.exe" "d:\招聘\scripts\test_pc_wechat.py"
) else (
    python "d:\招聘\scripts\test_pc_wechat.py"
)

echo.
echo ==========================================================
pause

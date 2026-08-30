@echo off
chcp 65001 >nul
title AI Job Hunter Pro - WeChat & Feishu Bot Test Suite

echo ==========================================================
echo [AI Job Hunter Pro] WeChat and Feishu Bot Test Suite
echo ==========================================================
echo.

if exist "d:\招聘\.venv\Scripts\python.exe" (
    "d:\招聘\.venv\Scripts\python.exe" "d:\招聘\scripts\test_bots.py"
) else (
    python "d:\招聘\scripts\test_bots.py"
)

echo.
echo ==========================================================
pause

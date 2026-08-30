@echo off
title AI Job Hunter Pro - Live Multi-Turn HR Chat Responder
cd /d "%~dp0"

echo ==========================================================
echo [AI Job Hunter Pro] Live Multi-Turn HR Chat Responder
echo ==========================================================
echo.
echo Connecting to live Chrome window and listening for HR messages...
echo.

if exist ".\.venv\Scripts\python.exe" (
    ".\.venv\Scripts\python.exe" run_live_chat_responder.py
) else (
    python run_live_chat_responder.py
)

pause

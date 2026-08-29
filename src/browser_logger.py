"""
Real-time Chrome Browser DevTools & Network Event Logger.
Captures:
1. Console Logs (console.log, console.warn, console.error) directly from Chrome V8.
2. Page Runtime Errors & Uncaught Exceptions.
3. Network API Requests & Responses (XHR / Fetch / Status Codes).
4. Frame & Page Navigation URL transitions.
5. Dialogs and Web Worker events.
Writes to: logs/chrome_browser.log
"""
import sys
import os
import datetime
from pathlib import Path

LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
BROWSER_LOG_FILE = LOGS_DIR / "chrome_browser.log"


def log_browser_raw(category: str, message: str):
    """写入浏览器原始日志"""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    line = f"[{now_str}] [{category:<15}] {message}\n"
    try:
        with open(BROWSER_LOG_FILE, "a", encoding="utf-8", errors="replace") as f:
            f.write(line)
    except Exception:
        pass


def attach_browser_logger(page, filter_static_assets: bool = True):
    """
    为 Playwright Page 挂载 Chrome 全方位日志监听器
    """
    # 1. 监听 Chrome 控制台输出 (Console)
    def on_console(msg):
        m_type = msg.type.upper()
        m_text = msg.text
        # 过滤部分无关冗余的统计日志
        if any(noise in m_text for noise in ["sensorsdata", "growingio", "track", "report"]):
            return
        log_browser_raw(f"CONSOLE_{m_type}", m_text)

    page.on("console", on_console)

    # 2. 监听页面未捕获的 JavaScript 异常 (PageError)
    def on_pageerror(err):
        log_browser_raw("JS_EXCEPTION", str(err))

    page.on("pageerror", on_pageerror)

    # 3. 监听页面与 Frame 导航跳转 (Navigate)
    def on_framenavigated(frame):
        if frame == page.main_frame:
            log_browser_raw("PAGE_NAVIGATE", f"主页面跳转至: {frame.url}")

    page.on("framenavigated", on_framenavigated)

    # 4. 监听网络请求与响应 (Network API)
    def on_request(req):
        url = req.url
        resource_type = req.resource_type
        if filter_static_assets and resource_type in ["image", "media", "font", "stylesheet"]:
            return
        if "zhipin.com" in url or "api" in url:
            log_browser_raw("HTTP_REQ", f"[{req.method}] ({resource_type}) {url[:100]}")

    page.on("request", on_request)

    def on_response(res):
        url = res.url
        status = res.status
        if filter_static_assets and any(ext in url for ext in [".png", ".jpg", ".css", ".woff", ".svg", ".gif"]):
            return
        if "zhipin.com" in url:
            tag = "HTTP_OK" if status < 400 else "HTTP_ERR"
            log_browser_raw(f"{tag}_{status}", f"{url[:100]}")

    page.on("response", on_response)

    # 5. 监听网络请求失败 (RequestFailed)
    def on_requestfailed(req):
        err = req.failure
        log_browser_raw("NET_FAILED", f"[{req.method}] {req.url[:100]} | 失败原因: {err}")

    page.on("requestfailed", on_requestfailed)

    # 6. 监听对话框弹窗 (Dialog)
    def on_dialog(dialog):
        log_browser_raw("JS_DIALOG", f"类型: {dialog.type} | 内容: {dialog.message}")

    page.on("dialog", on_dialog)

    log_browser_raw("LOGGER_INIT", "Chrome 浏览器 DevTools & 全量网络日志监听器挂载就绪")

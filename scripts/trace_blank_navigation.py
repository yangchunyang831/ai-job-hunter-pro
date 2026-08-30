"""
Trace why BOSS 直聘 navigates to about:blank.
"""
import sys
import os
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

user_data_dir = r"C:\chrome_debug_profile"
chat_url = "https://www.zhipin.com/web/geek/chat"

async def main():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            channel="chrome",
            ignore_default_args=["--enable-automation"],
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--no-first-run",
                "--no-default-browser-check"
            ]
        )
        page = context.pages[0]
        
        page.on("console", lambda msg: print(f"[CONSOLE {msg.type}] {msg.text}"))
        page.on("framenavigated", lambda frame: print(f"[NAVIGATED] {frame.url}"))
        page.on("pageerror", lambda err: print(f"[PAGE ERROR] {err}"))
        
        print(f"Navigating to {chat_url}...")
        try:
            await page.goto(chat_url, wait_until="commit", timeout=60000)
        except Exception as e:
            print(f"Goto error: {e}")
            
        for i in range(10):
            await asyncio.sleep(1)
            print(f"T+{i+1}s URL: {page.url}")
            
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())

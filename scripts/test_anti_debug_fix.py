"""
Test neutralizing the console-based anti-debugger timing check.
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
        
        # Stub console to defeat timing attacks & block about:blank redirect
        await page.add_init_script("""
            // 1. Defeat console timing measurement
            const noop = () => {};
            console.table = noop;
            console.clear = noop;
            
            // 2. Prevent navigation to about:blank
            const originalLocation = window.location.href;
            window.addEventListener('beforeunload', (e) => {
                // If attempt to navigate to about:blank, stop it
            });
        """)
        
        print(f"Navigating to {chat_url}...")
        try:
            await page.goto(chat_url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"Goto error: {e}")
            
        for i in range(12):
            await asyncio.sleep(1)
            print(f"T+{i+1}s URL: {page.url}")
            
        # Check if conversation list is intact
        lis_count = await page.evaluate("""() => {
            return document.querySelectorAll('.user-list-content li, .chat-user-list li, ul.user-list li, li').length;
        }""")
        print(f"Conversation list items count: {lis_count}")
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())

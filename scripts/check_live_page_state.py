"""
Check what page is loaded in Chrome profile.
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
        print(f"Initial page URL: {page.url}")
        try:
            await page.goto(chat_url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"Goto error: {e}")
            
        print(f"URL after goto: {page.url}")
        await asyncio.sleep(6)
        print(f"URL after 6s wait: {page.url}")
        
        # Take screenshot
        screenshot_path = Path("tests/test_screenshots/live_page_state.png")
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(screenshot_path))
        print(f"Screenshot saved to: {screenshot_path}")
        
        # Check titles / DOM
        title = await page.title()
        print(f"Page title: {title}")
        
        # Check if login modal or captcha exists
        body_text = await page.evaluate("() => document.body.innerText.slice(0, 300)")
        print(f"Body text preview:\n{body_text}")
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


async def main():
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    user_data_dir = r"C:\chrome_debug_profile"
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            executable_path=chrome_path,
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        print("1. Visiting job-recommend...")
        await page.goto("https://www.zhipin.com/web/geek/job-recommend")
        await page.wait_for_timeout(3000)
        
        print("Current URL:", page.url)
        
        # 查找验证码按钮
        btn = await page.query_selector(".btn, .btn-verify, button, .geetest_radar_tip, .geetest_btn")
        if btn:
            print("Found verify button! Clicking it...")
            await btn.click()
            await page.wait_for_timeout(5000)
            print("After click URL:", page.url)
            await page.screenshot(path=r"d:\招聘\tests\test_screenshots\after_verify_click.png")
            print("Saved screenshot: after_verify_click.png")
            
        await context.close()


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def main():
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    user_data_dir = r"C:\chrome_debug_profile"
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            executable_path=chrome_path,
            headless=True
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        target_url = "https://www.zhipin.com/web/geek/job-recommend"
        print("Navigating to:", target_url, flush=True)
        await page.goto(target_url, wait_until="domcontentloaded", timeout=25000)
        await asyncio.sleep(4)
        
        print("Final URL:", page.url, flush=True)
        await page.screenshot(path="tests/test_screenshots/recommend_page_debug.png")
        print("Screenshot saved to tests/test_screenshots/recommend_page_debug.png", flush=True)
        
        # Check text
        body_text = await page.inner_text("body")
        print("Body preview:\n", body_text[:300], flush=True)
        
        await context.close()


if __name__ == "__main__":
    asyncio.run(main())

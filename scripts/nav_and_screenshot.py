import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = b.contexts[0].pages[0]
        
        print("Navigating to https://www.zhipin.com/web/geek/job?query=英语客服&city=101020100 ...", flush=True)
        await page.goto("https://www.zhipin.com/web/geek/job?query=%E8%8B%B1%E8%AF%AD%E5%AE%A2%E6%9C%8D&city=101020100", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        await page.screenshot(path="tests/test_screenshots/job_page_loaded.png")
        print("Screenshot saved to tests/test_screenshots/job_page_loaded.png", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

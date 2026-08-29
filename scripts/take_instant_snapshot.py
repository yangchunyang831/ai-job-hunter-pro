import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        
        print(f"Total open pages: {len(context.pages)}", flush=True)
        for idx, page in enumerate(context.pages, 1):
            print(f"Page {idx}: URL={page.url} | Title={await page.title()}", flush=True)
            await page.screenshot(path=f"tests/test_screenshots/live_tab_{idx}.png")
            print(f"  Screenshot saved to tests/test_screenshots/live_tab_{idx}.png", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

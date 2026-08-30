import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = b.contexts[0].pages[0]
        
        print("Waiting for page header...", flush=True)
        await page.wait_for_selector("div.header-search, .search-form, [class*='header'], [class*='job']", timeout=15000)
        print("Header rendered!", flush=True)
        
        await asyncio.sleep(2)
        await page.screenshot(path="tests/test_screenshots/hydrated_live_screen.png")
        print("Screenshot saved to tests/test_screenshots/hydrated_live_screen.png", flush=True)
        
        cards = await page.query_selector_all(".job-card-wrapper, .job-card-box, li.job-card, .job-list-box li, [class*='job-card']")
        print(f"Captured {len(cards)} cards!", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

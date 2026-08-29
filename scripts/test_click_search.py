import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = b.contexts[0].pages[0]
        
        print("1. Clicking search button on page...", flush=True)
        # Position of the green [搜索] button in the screenshot is around (850, 95)
        # Or selector .btn-search
        await page.click(".btn-search, [class*='btn-search'], button:has-text('搜索')")
        print("   Clicked search button!", flush=True)
        
        await asyncio.sleep(4)
        
        print("2. Extracting cards...", flush=True)
        await page.screenshot(path="tests/test_screenshots/live_after_btn_click.png")
        print("Screenshot saved to tests/test_screenshots/live_after_btn_click.png", flush=True)
        
        # Check text in body
        cards = await page.query_selector_all(".job-card-wrapper, .job-card-box, li.job-card, .job-list-box li, [class*='job-card']")
        print(f"Total cards found: {len(cards)}", flush=True)
        for i, c in enumerate(cards[:5], 1):
            txt = (await c.inner_text()).replace("\n", " | ")
            print(f"  [Card {i}]: {txt[:90]}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

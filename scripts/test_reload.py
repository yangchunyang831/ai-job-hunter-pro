import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = b.contexts[0].pages[0]
        
        print("1. Reloading active page...", flush=True)
        await page.reload(wait_until="domcontentloaded", timeout=25000)
        await asyncio.sleep(5)
        
        print("2. Page Title:", await page.title(), flush=True)
        print("   Page URL:", page.url, flush=True)
        await page.screenshot(path="tests/test_screenshots/live_reloaded.png")
        print("Screenshot saved to tests/test_screenshots/live_reloaded.png", flush=True)
        
        cards = await page.query_selector_all(".job-card-wrapper, .job-card-box, li.job-card, .job-list-box li, [class*='job-card']")
        print(f"Total cards found: {len(cards)}", flush=True)
        for i, c in enumerate(cards[:5], 1):
            txt = (await c.inner_text()).replace("\n", " | ")
            print(f"  [Card {i}]: {txt[:90]}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

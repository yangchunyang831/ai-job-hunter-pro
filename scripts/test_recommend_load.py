import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = b.contexts[0].pages[0]
        
        print("Navigating to Recommendation Feed: https://www.zhipin.com/web/geek/job-recommend", flush=True)
        await page.goto("https://www.zhipin.com/web/geek/job-recommend", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        await page.screenshot(path="tests/test_screenshots/recommend_feed.png")
        print("Screenshot saved to tests/test_screenshots/recommend_feed.png", flush=True)
        
        cards = await page.query_selector_all(".job-card-wrapper, .job-card-box, li.job-card, .job-list-box li, [class*='job-card']")
        print(f"Total cards found in recommendation stream: {len(cards)}", flush=True)
        for i, c in enumerate(cards[:8], 1):
            txt = (await c.inner_text()).replace("\n", " | ")
            print(f"  [Card {i}]: {txt[:90]}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

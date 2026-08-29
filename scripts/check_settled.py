import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = b.contexts[0].pages[0]
        await asyncio.sleep(3)
        print("Current Title:", await page.title(), flush=True)
        print("Current URL:", page.url, flush=True)
        await page.screenshot(path="tests/test_screenshots/live_tab_1_settled.png")
        print("Screenshot saved to tests/test_screenshots/live_tab_1_settled.png", flush=True)
        
        cards = await page.query_selector_all("li.job-card, .job-card-box, .job-card-wrapper, [class*='job-card']")
        print("Cards count:", len(cards), flush=True)
        for i, c in enumerate(cards[:5], 1):
            txt = (await c.inner_text()).replace("\n", " ")
            print(f"Card {i}: {txt[:80]}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

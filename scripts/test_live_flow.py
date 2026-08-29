import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = b.contexts[0]
        page = context.pages[0]
        
        print("1. Waiting for current navigation to complete...", flush=True)
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=15000)
        except Exception:
            pass
            
        await asyncio.sleep(4)
        
        print(f"2. Loaded Page URL: {page.url} | Title: {await page.title()}", flush=True)
        await page.screenshot(path="tests/test_screenshots/live_flow_settled.png")
        print("Screenshot saved to tests/test_screenshots/live_flow_settled.png", flush=True)
        
        # Read cards
        cards = await page.query_selector_all(".job-card-wrapper, .job-card-box, li.job-card, .job-list-box li, [class*='job-card']")
        print(f"3. Extracted {len(cards)} card elements:", flush=True)
        for i, c in enumerate(cards[:6], 1):
            txt = (await c.inner_text()).replace("\n", " | ")
            print(f"  [Card {i}]: {txt[:90]}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

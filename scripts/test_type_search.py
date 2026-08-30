import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = b.contexts[0].pages[0]
        
        print("1. Focusing search box...", flush=True)
        search_ipt = page.locator(".ipt-search, input[placeholder*='搜索'], .search-form input").first
        if await search_ipt.is_visible():
            await search_ipt.click()
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Backspace")
            await page.keyboard.type("英语客服", delay=100)
            print("   Typed '英语客服' into search input!", flush=True)
            await page.keyboard.press("Enter")
            print("   Pressed Enter!", flush=True)
            
        await asyncio.sleep(4)
        
        # Take screenshot
        await page.screenshot(path="tests/test_screenshots/after_enter_search.png")
        print("Screenshot saved to tests/test_screenshots/after_enter_search.png", flush=True)
        
        cards = await page.query_selector_all(".job-card-wrapper, .job-card-box, li.job-card, .job-list-box li, [class*='job-card']")
        print(f"Total cards found: {len(cards)}", flush=True)
        for i, c in enumerate(cards[:5], 1):
            try:
                txt = (await c.inner_text()).replace("\n", " | ")
                print(f"  [Card {i}]: {txt[:90]}", flush=True)
            except Exception:
                pass


if __name__ == "__main__":
    asyncio.run(main())

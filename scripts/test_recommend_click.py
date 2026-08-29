import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0]
        
        print("1. Clicking '推荐' tab at top left...", flush=True)
        rec_tab = page.locator("a:has-text('推荐'), [class*='recommend']").first
        if await rec_tab.is_visible():
            await rec_tab.click()
            print("   Clicked '推荐' tab!", flush=True)
        else:
            await page.goto("https://www.zhipin.com/web/geek/job-recommend", wait_until="domcontentloaded")
            print("   Navigated to job-recommend!", flush=True)
            
        await asyncio.sleep(4)
        
        print("2. Extracting cards and city tags...", flush=True)
        await page.screenshot(path="tests/test_screenshots/recommend_tab_result.png")
        print("Screenshot saved to tests/test_screenshots/recommend_tab_result.png", flush=True)
        
        card_elems = await page.query_selector_all(".job-card-wrapper, .job-card-box, li.job-card, .job-list-box li, .job-card-left, .job-primary, [class*='job-card']")
        print(f"Found {len(card_elems)} card elements:", flush=True)
        
        for idx, c in enumerate(card_elems[:8], 1):
            txt = (await c.inner_text()).replace("\n", " | ")
            print(f"  [{idx}]: {txt[:90]}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

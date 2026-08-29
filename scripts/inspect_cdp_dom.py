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
        
        print("Page URL:", page.url, flush=True)
        print("Page Title:", await page.title(), flush=True)
        
        # Screenshot
        await page.screenshot(path="tests/test_screenshots/cdp_active_page.png")
        print("Screenshot saved to tests/test_screenshots/cdp_active_page.png", flush=True)
        
        # Find selectors
        for sel in [".job-card-wrapper", ".job-card-box", "li.job-card", ".job-list-box li", ".job-card-left", ".job-primary", "[class*='job-card']", "a[href*='job_detail']"]:
            elems = await page.query_selector_all(sel)
            print(f"Selector '{sel}': {len(elems)} elements", flush=True)
            if elems:
                txt = (await elems[0].inner_text()).replace("\n", " | ")
                print(f"  First item: {txt[:80]}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

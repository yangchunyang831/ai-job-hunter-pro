import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = b.contexts[0].pages[0]
        
        print("Page URL:", page.url, flush=True)
        
        # Test all selectors
        selectors = [
            ".job-card-wrapper",
            ".job-card-box",
            "li.job-card",
            ".job-list-box li",
            ".job-primary",
            "[class*='job-card']",
            ".card-item",
            "ul.job-list-box > li"
        ]
        
        for sel in selectors:
            elems = await page.query_selector_all(sel)
            print(f"Selector '{sel}': {len(elems)} elements", flush=True)
            if elems:
                sample_txt = (await elems[0].inner_text()).replace("\n", " | ")
                print(f"   Sample 1: {sample_txt[:100]}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

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
        
        print("1. Current page URL:", page.url, flush=True)
        
        # Take screenshot of whatever is on screen right now!
        await page.screenshot(path="tests/test_screenshots/live_after_click.png")
        print("2. Screenshot saved to tests/test_screenshots/live_after_click.png", flush=True)
        
        # Check all pages in context
        print(f"3. Total Pages in Context: {len(context.pages)}", flush=True)
        for i, pg in enumerate(context.pages, 1):
            print(f"   [Page {i}] {pg.url}", flush=True)
            # Check if 立即沟通 is on this page
            btn = pg.locator("a:has-text('立即沟通'), button:has-text('立即沟通'), .btn-startchat, .op-btn-chat").first
            if await btn.is_visible():
                btn_txt = (await btn.inner_text()).strip()
                print(f"   🎉 Found chat button on Page {i}: 【{btn_txt}】!", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

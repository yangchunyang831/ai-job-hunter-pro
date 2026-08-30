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
        
        await page.bring_to_front()
        print("1. Reloading page and waiting for DOM hydration...", flush=True)
        await page.reload(wait_until="networkidle", timeout=30000)
        
        print("2. Current Title:", await page.title(), flush=True)
        print("   Current URL:", page.url, flush=True)
        
        body = await page.evaluate("document.body.innerText")
        print(f"   Body text length: {len(body)}", flush=True)
        print(f"   Body text snippet: {repr(body[:200])}", flush=True)
        
        await page.screenshot(path="tests/test_screenshots/hydrated_page.png")
        print("Screenshot saved to tests/test_screenshots/hydrated_page.png", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

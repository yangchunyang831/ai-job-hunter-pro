import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = b.contexts[0]
        print(f"Total open pages: {len(context.pages)}", flush=True)
        for i, page in enumerate(context.pages, 1):
            print(f"Page {i}: URL={page.url} | Title={await page.title()}", flush=True)
            # Evaluate document.readyState
            ready = await page.evaluate("document.readyState")
            print(f"   ReadyState: {ready}", flush=True)
            body_html = await page.evaluate("document.body.innerHTML")
            print(f"   Body HTML length: {len(body_html)}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

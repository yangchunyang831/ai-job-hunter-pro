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
        print("Page Title:", await page.title(), flush=True)
        body = await page.evaluate("document.body ? document.body.innerText : 'NO BODY'")
        print("Body Text Preview:", repr(body[:200]), flush=True)


if __name__ == "__main__":
    asyncio.run(main())

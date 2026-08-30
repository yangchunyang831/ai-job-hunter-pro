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
        
        await page.screenshot(path="tests/test_screenshots/current_debug_state.png")
        print("Screenshot saved to tests/test_screenshots/current_debug_state.png", flush=True)
        
        # Query all elements
        info = await page.evaluate("""() => {
            return {
                bodyText: document.body ? document.body.innerText.slice(0, 300) : '',
                allDivsWithClass: Array.from(document.querySelectorAll('div[class]')).map(d => d.className).slice(0, 20),
                listCount: document.querySelectorAll('li').length,
                anchorCount: document.querySelectorAll('a').length
            };
        }""")
        print("Page Info:", info, flush=True)


if __name__ == "__main__":
    asyncio.run(main())

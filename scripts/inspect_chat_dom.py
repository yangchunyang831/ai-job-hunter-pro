import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = b.contexts[0].pages[0]
        
        await page.screenshot(path="tests/test_screenshots/live_chat_page.png")
        print("Screenshot saved to tests/test_screenshots/live_chat_page.png", flush=True)
        
        dom = await page.evaluate("""() => {
            const listItems = Array.from(document.querySelectorAll('li, div[class*="user"], div[class*="chat"], div[class*="item"]')).map(el => ({
                tag: el.tagName,
                cls: el.className,
                text: el.innerText ? el.innerText.replace(/\\n/g, ' | ').slice(0, 80) : ''
            })).filter(x => x.text.length > 5);
            return listItems.slice(0, 20);
        }""")
        print("DOM items on Chat page:", dom, flush=True)


if __name__ == "__main__":
    asyncio.run(main())

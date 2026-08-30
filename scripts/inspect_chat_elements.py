import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = b.contexts[0].pages[0]
        
        await page.screenshot(path="tests/test_screenshots/active_chat_room.png")
        print("Screenshot saved to tests/test_screenshots/active_chat_room.png", flush=True)
        
        # Query all elements on page with text
        elements = await page.evaluate("""() => {
            const res = [];
            document.querySelectorAll('*').forEach(el => {
                if (el.children.length === 0 && el.innerText && el.innerText.trim().length > 3) {
                    res.push({
                        tag: el.tagName,
                        cls: el.className,
                        parentCls: el.parentElement ? el.parentElement.className : '',
                        text: el.innerText.trim()
                    });
                }
            });
            return res.slice(0, 40);
        }""")
        print("Elements found:", elements, flush=True)


if __name__ == "__main__":
    asyncio.run(main())

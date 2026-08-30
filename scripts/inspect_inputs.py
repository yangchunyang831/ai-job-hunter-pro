import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = b.contexts[0].pages[0]
        
        inputs = await page.evaluate("""() => {
            const res = [];
            document.querySelectorAll('input').forEach(i => {
                res.push({
                    tagName: i.tagName,
                    className: i.className,
                    placeholder: i.placeholder,
                    value: i.value,
                    type: i.type
                });
            });
            return res;
        }""")
        print("Inputs on page:", inputs, flush=True)


if __name__ == "__main__":
    asyncio.run(main())

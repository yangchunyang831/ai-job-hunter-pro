import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = b.contexts[0].pages[0]
        
        print("Waiting for chat room to load...", flush=True)
        for i in range(15):
            await asyncio.sleep(1.0)
            text = await page.evaluate("() => document.body ? document.body.innerText : ''")
            if "加载中" not in text and len(text) > 10:
                print(f"🎉 Chat room fully loaded at second {i+1}!", flush=True)
                break
                
        await page.screenshot(path="tests/test_screenshots/chat_room_hydrated.png")
        print("Screenshot saved to tests/test_screenshots/chat_room_hydrated.png", flush=True)
        
        # Extract chat items
        items = await page.evaluate("""() => {
            const res = [];
            document.querySelectorAll('li, div[class*="item"], div[class*="user"]').forEach(el => {
                const txt = el.innerText ? el.innerText.replace(/\\n/g, ' | ').trim() : '';
                if (txt.length > 5 && txt.length < 150 && (txt.includes('上海') || txt.includes('携程') || txt.includes('客服') || txt.includes('先生') || txt.includes('女士'))) {
                    res.push({
                        tag: el.tagName,
                        cls: el.className,
                        txt: txt
                    });
                }
            });
            return res;
        }""")
        print("Found chat conversations:", items[:10], flush=True)


if __name__ == "__main__":
    asyncio.run(main())

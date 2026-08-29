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
        
        chat_url = "https://www.zhipin.com/web/geek/chat"
        print("Navigating to Chat Center:", chat_url, flush=True)
        await page.goto(chat_url, wait_until="domcontentloaded", timeout=25000)
        await asyncio.sleep(4)
        
        print("Chat Page URL:", page.url, flush=True)
        print("Chat Page Title:", await page.title(), flush=True)
        await page.screenshot(path="tests/test_screenshots/live_chat_center_status.png")
        print("Screenshot saved to tests/test_screenshots/live_chat_center_status.png", flush=True)
        
        # Check conversations
        chats = await page.query_selector_all(".geek-chat-item, .chat-item, [class*='chat-item'], .user-list li")
        print(f"Active conversations found: {len(chats)}", flush=True)
        for i, c in enumerate(chats[:5], 1):
            txt = (await c.inner_text()).replace("\n", " | ")
            print(f"  [Chat {i}]: {txt[:80]}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

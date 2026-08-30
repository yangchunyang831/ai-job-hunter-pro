import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = b.contexts[0].pages[0]
        
        print("1. Current URL:", page.url, flush=True)
        
        # Navigate to chat page
        print("2. Navigating to https://www.zhipin.com/web/geek/chat ...", flush=True)
        await page.goto("https://www.zhipin.com/web/geek/chat", wait_until="domcontentloaded")
        await asyncio.sleep(4)
        
        # Take screenshot of chat page
        await page.screenshot(path="tests/test_screenshots/chat_inbox_view.png")
        print("Screenshot saved to tests/test_screenshots/chat_inbox_view.png", flush=True)
        
        # Extract conversations in inbox
        conv_info = await page.evaluate("""() => {
            const items = [];
            document.querySelectorAll('.chat-user-list li, .user-list-content li, [class*="chat-item"], [class*="conversation-item"]').forEach(el => {
                items.push({
                    text: el.innerText ? el.innerText.replace(/\\n/g, ' | ').slice(0, 120) : '',
                    hasUnread: !!el.querySelector('.badge, .num, .unread, [class*="badge"]')
                });
            });
            return items;
        }""")
        print("Conversations found in Chat Inbox:", conv_info, flush=True)


if __name__ == "__main__":
    asyncio.run(main())

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
        
        print("1. Current URL:", page.url, flush=True)
        
        # Locate conversation items via locator
        list_loc = page.locator(".user-list-content li, .chat-user-list li, .geek-chat-list li, ul.user-list li, .main-list li")
        count = await list_loc.count()
        print(f"2. Total conversations in inbox: {count}", flush=True)
        
        for i in range(count):
            item = list_loc.nth(i)
            txt = (await item.inner_text()).replace("\n", " | ")
            print(f"   👉 [Conversation {i+1}]: {txt[:80]}", flush=True)
            
            # Click conversation item
            await item.click()
            await asyncio.sleep(2.0)
            
            # Extract messages in active conversation
            msg_loc = page.locator(".item-friend .text, .item-friend, .chat-item-hr, .message-card")
            msg_count = await msg_loc.count()
            print(f"      Total messages in room: {msg_count}", flush=True)
            if msg_count > 0:
                for m in range(min(msg_count, 3)):
                    m_txt = (await msg_loc.nth(m).inner_text()).strip().replace("\n", " ")
                    print(f"      [Msg {m+1}]: \"{m_txt[:60]}\"", flush=True)
                    
        await page.screenshot(path="tests/test_screenshots/inbox_conversations_inspected.png")
        print("\nScreenshot saved to tests/test_screenshots/inbox_conversations_inspected.png", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

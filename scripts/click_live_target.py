import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = b.contexts[0].pages[0]
        
        print("1. Clicking the first job card on the left list (coordinate ~ 230, 280)...", flush=True)
        await page.mouse.click(230, 280)
        await asyncio.sleep(3)
        
        await page.screenshot(path="tests/test_screenshots/detail_opened.png")
        print("Screenshot saved to tests/test_screenshots/detail_opened.png", flush=True)
        
        # Look for 立即沟通 button
        chat_btns = await page.query_selector_all("a:has-text('立即沟通'), button:has-text('立即沟通'), .btn-startchat, [class*='btn-startchat'], .op-btn")
        print(f"Found {len(chat_btns)} chat buttons on page!", flush=True)
        for i, btn in enumerate(chat_btns, 1):
            print(f"  Button {i}: text='{await btn.inner_text()}' visible={await btn.is_visible()}", flush=True)
            if await btn.is_visible():
                print("👉 Clicking 立即沟通 button now!", flush=True)
                await btn.click()
                await asyncio.sleep(2)
                
                # Check for confirm modal
                confirm_btn = page.locator(".dialog-startchat .btn-sure, button:has-text('确定'), button:has-text('发送'), button:has-text('确认沟通')").first
                if await confirm_btn.is_visible():
                    print("👉 Confirming startchat dialog!", flush=True)
                    await confirm_btn.click()
                    await asyncio.sleep(2)
                    
                await page.screenshot(path="tests/test_screenshots/chat_sent_success.png")
                print("Screenshot saved to tests/test_screenshots/chat_sent_success.png", flush=True)
                break


if __name__ == "__main__":
    asyncio.run(main())

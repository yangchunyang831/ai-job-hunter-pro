"""
Test and inspect the exact DOM elements of BOSS 直聘's Resume Preview & Confirmation Dialog.
"""
import sys
import os
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

user_data_dir = r"C:\chrome_debug_profile"
chat_url = "https://www.zhipin.com/web/geek/chat"

async def main():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            channel="chrome",
            ignore_default_args=["--enable-automation"],
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--no-first-run",
                "--no-default-browser-check"
            ]
        )
        page = context.pages[0]
        
        # Anti-timing fix
        await page.add_init_script("""
            const noop = () => {};
            console.table = noop;
            console.clear = noop;
        """)
        
        print("Navigating to chat...")
        await page.goto(chat_url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(4.0)
        
        # Click on the first English CS HR (e.g. 欧阳先生 or 翟先生)
        await page.evaluate("""() => {
            const lis = document.querySelectorAll('.user-list-content li, .chat-user-list li, ul.user-list li, li');
            for (let li of lis) {
                const txt = li.innerText || '';
                if (txt.includes('欧阳') || txt.includes('翟') || txt.includes('启页') || txt.includes('览川')) {
                    li.click();
                    break;
                }
            }
        }""")
        await asyncio.sleep(2.5)
        
        # Check current DOM for cards, modals, buttons
        dom_info = await page.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('button, a, div[role="button"], .dialog-wrap, .boss-dialog, [class*="dialog"], [class*="modal"], [class*="pop"]')).map(el => {
                return {
                    tag: el.tagName,
                    cls: el.className,
                    text: (el.innerText || '').slice(0, 100).replace(/\\n/g, ' '),
                    rect: el.getBoundingClientRect()
                };
            }).filter(item => item.text.length > 0 && item.rect.width > 0);
            
            return {
                buttons: btns,
                bodyText: document.body.innerText.slice(0, 800)
            };
        }""")
        
        print("\n=== Visible Buttons & Modals in Chat ===")
        for b in dom_info["buttons"]:
            print(f"[{b['tag']}.{b['cls']}] '{b['text']}' (w={b['rect']['width']}, h={b['rect']['height']})")
            
        # Take a screenshot
        screenshot_path = Path("tests/test_screenshots/chat_resume_modal_inspect.png")
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(screenshot_path))
        print(f"\nScreenshot saved to: {screenshot_path}")
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())

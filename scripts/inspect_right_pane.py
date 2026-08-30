"""
Find all buttons inside .chat-conversation or modals in BOSS 直聘.
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
        
        await page.add_init_script("""
            const noop = () => {};
            console.table = noop;
            console.clear = noop;
        """)
        
        await page.goto(chat_url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(4.0)
        
        # Click 欧阳先生 or 翟先生 card
        clicked = await page.evaluate("""() => {
            const lis = document.querySelectorAll('.user-list-content li, .chat-user-list li, ul.user-list li, li');
            for (let li of lis) {
                const txt = li.innerText || '';
                if (txt.includes('欧阳') || txt.includes('翟') || txt.includes('启页') || txt.includes('览川')) {
                    li.click();
                    return txt.replace(/\\n/g, ' | ');
                }
            }
            return null;
        }""")
        print(f"Clicked HR card: {clicked}")
        await asyncio.sleep(3.0)
        
        # Dump all elements in right pane
        right_pane = await page.evaluate("""() => {
            const pane = document.querySelector('.chat-conversation, .chat-message-box, .chat-main, .main-content') || document.body;
            const buttons = Array.from(pane.querySelectorAll('button, .btn, [class*="btn"], .dialog-wrap, [class*="card"]')).map(el => {
                return {
                    tag: el.tagName,
                    cls: el.className,
                    text: (el.innerText || '').slice(0, 100).replace(/\\n/g, ' ')
                };
            }).filter(item => item.text.length > 0);
            
            return {
                buttons: buttons,
                textSummary: pane.innerText.slice(0, 1000)
            };
        }""")
        
        print("\n=== Right Pane Buttons & Elements ===")
        for b in right_pane["buttons"]:
            print(f"[{b['tag']}.{b['cls']}] '{b['text']}'")
            
        print("\n=== Text Summary in Right Pane ===")
        print(right_pane["textSummary"])
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())

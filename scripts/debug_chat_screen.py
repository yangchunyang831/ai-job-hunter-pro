import asyncio
import sys
import subprocess
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
user_data_dir = r"C:\chrome_debug_profile"
chat_url = "https://www.zhipin.com/web/geek/chat"


async def main():
    async with async_playwright() as p:
        browser = None
        for _ in range(3):
            try:
                browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                break
            except Exception:
                await asyncio.sleep(1.0)
                
        if not browser:
            print("Launching Chrome...", flush=True)
            subprocess.Popen([
                chrome_path,
                "--remote-debugging-port=9222",
                f"--user-data-dir={user_data_dir}",
                "--no-first-run",
                "--no-default-browser-check",
                chat_url
            ])
            for _ in range(12):
                await asyncio.sleep(1.0)
                try:
                    browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                    break
                except Exception:
                    pass
                    
        page = browser.contexts[0].pages[0]
        await page.bring_to_front()
        print("Current URL:", page.url, flush=True)
        
        if "web/geek/chat" not in page.url:
            print("Navigating to chat_url...", flush=True)
            await page.goto(chat_url, wait_until="domcontentloaded")
            await asyncio.sleep(4)
            
        await page.screenshot(path="tests/test_screenshots/chat_screen_debug.png")
        print("Screenshot saved to tests/test_screenshots/chat_screen_debug.png", flush=True)
        
        dom_res = await page.evaluate("""() => {
            const list = [];
            document.querySelectorAll('li, div[class*="user"], div[class*="chat"], div[class*="item"]').forEach(el => {
                const text = el.innerText ? el.innerText.replace(/\\n/g, ' | ').trim() : '';
                if (text.length > 5 && text.length < 150) {
                    list.push({
                        tag: el.tagName,
                        className: el.className,
                        text: text
                    });
                }
            });
            return list.slice(0, 20);
        }""")
        print("DOM Items:", dom_res, flush=True)


if __name__ == "__main__":
    asyncio.run(main())

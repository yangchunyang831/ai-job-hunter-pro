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
            print("Launching Chrome with robust CDP flags...", flush=True)
            subprocess.Popen([
                chrome_path,
                "--remote-debugging-port=9222",
                "--remote-allow-origins=*",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
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
                    
        print("Connected to browser!", flush=True)
        context = browser.contexts[0]
        pages = [pg for pg in context.pages if not pg.is_closed() and "zhipin.com" in pg.url]
        page = pages[0] if pages else context.pages[0]
        
        print("Active Page URL:", page.url, flush=True)
        await asyncio.sleep(5)
        
        await page.screenshot(path="tests/test_screenshots/cdp_flag_verified.png")
        print("Screenshot saved to tests/test_screenshots/cdp_flag_verified.png", flush=True)
        
        text = await page.evaluate("() => document.body ? document.body.innerText : ''")
        print(f"Page text length: {len(text)}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

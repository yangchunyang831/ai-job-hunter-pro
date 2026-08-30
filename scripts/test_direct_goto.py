import asyncio
import sys
import subprocess
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
user_data_dir = r"C:\chrome_debug_profile"
target_url = "https://www.zhipin.com/web/geek/job?query=%E8%8B%B1%E8%AF%AD%E5%AE%A2%E6%9C%8D&city=101020100"


async def main():
    async with async_playwright() as p:
        browser = None
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        except Exception:
            pass
            
        if not browser:
            print("1. Launching Chrome...", flush=True)
            subprocess.Popen([
                chrome_path,
                "--remote-debugging-port=9222",
                f"--user-data-dir={user_data_dir}",
                "--no-first-run",
                "--no-default-browser-check",
                target_url
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
        print("2. Navigating directly to target_url...", flush=True)
        await page.goto(target_url, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        await page.screenshot(path="tests/test_screenshots/direct_goto_result.png")
        print("Screenshot saved to tests/test_screenshots/direct_goto_result.png", flush=True)
        
        cards = await page.query_selector_all(".job-card-wrapper, .job-card-box, li.job-card, .job-list-box li, [class*='job-card']")
        print(f"Total cards captured: {len(cards)}", flush=True)
        for i, c in enumerate(cards[:5], 1):
            txt = (await c.inner_text()).replace("\n", " | ")
            print(f"  [Card {i}]: {txt[:90]}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

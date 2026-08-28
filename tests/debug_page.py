import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def debug_page():
    console_logs = []
    async with async_playwright() as p:
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        browser = await p.chromium.launch(headless=True, executable_path=chrome_path)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda exc: console_logs.append(f"[EXCEPTION] {exc}"))

        print("Navigating to http://127.0.0.1:8765 ...")
        await page.goto("http://127.0.0.1:8765", wait_until="load")
        await page.wait_for_timeout(3000)

        html = await page.content()
        print(f"HTML length: {len(html)}")
        print("\n--- Console Logs ---")
        for log in console_logs:
            print(log)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_page())

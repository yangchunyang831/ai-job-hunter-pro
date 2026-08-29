import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def main():
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    user_data_dir = r"C:\chrome_debug_profile"
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            executable_path=chrome_path,
            headless=True
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        print("Navigating to https://www.zhipin.com ...", flush=True)
        try:
            resp = await page.goto("https://www.zhipin.com", wait_until="load", timeout=30000)
            print("Status:", resp.status if resp else "None", flush=True)
            print("URL:", page.url, flush=True)
            print("Title:", await page.title(), flush=True)
        except Exception as e:
            print("Error during goto:", e, flush=True)
            
        await context.close()


if __name__ == "__main__":
    asyncio.run(main())

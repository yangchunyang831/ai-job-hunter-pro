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
        
        target_url = "https://www.zhipin.com/web/geek/job?query=%E6%B5%B7%E5%A4%96%E5%AE%A2%E6%9C%8D&city=101020100"
        print("1. Navigating to:", target_url, flush=True)
        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
        except Exception:
            pass
        
        print("2. Waiting for client-side navigation and Vue hydration to settle...", flush=True)
        cards = []
        for sec in range(25):
            await asyncio.sleep(1.0)
            
            # Catch all execution context destruction during client-side redirects
            try:
                cur_url = page.url
                if "verify.html" in cur_url:
                    print(f"   Captcha detected on second {sec+1} at {cur_url}", flush=True)
                    continue
                    
                if sec % 3 == 0:
                    try:
                        await page.mouse.wheel(0, 300)
                    except Exception:
                        pass
                        
                card_elems = await page.query_selector_all(".job-card-wrapper, .job-card-box, li.job-card, .job-list-box li, [class*='job-card']")
                for c in card_elems:
                    try:
                        txt = (await c.inner_text()).strip()
                        if len(txt) > 15 and any(k in txt for k in ["K", "k", "薪", "元", "面议"]):
                            cards.append(c)
                    except Exception:
                        pass
                if cards:
                    print(f"🎉 Fully rendered {len(cards)} cards at second {sec+1}! Final URL: {page.url}", flush=True)
                    break
            except Exception as e:
                # Execution context destroyed during redirect - seamlessly retry next second
                continue
                
        await page.screenshot(path="tests/test_screenshots/direct_geek_rendered.png")
        print("Screenshot saved to tests/test_screenshots/direct_geek_rendered.png", flush=True)
        
        for idx, c in enumerate(cards[:5], 1):
            try:
                txt = (await c.inner_text()).replace("\n", " | ")
                print(f"  Card {idx}: {txt[:80]}...", flush=True)
            except Exception:
                pass
            
        await context.close()


if __name__ == "__main__":
    asyncio.run(main())

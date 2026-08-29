import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0]
        
        print("1. Focusing search box and clicking search button...", flush=True)
        try:
            search_btn = page.locator(".btn-search, button:has-text('搜索'), a:has-text('搜索'), [class*='search-btn']").first
            if await search_btn.is_visible():
                await search_btn.click()
                print("   Clicked search button successfully!", flush=True)
        except Exception as e:
            print("   Search button click notice:", e)
            
        print("2. Waiting for navigation and card hydration to settle...", flush=True)
        cards = []
        for sec in range(25):
            await asyncio.sleep(1.0)
            try:
                if sec % 2 == 0:
                    try:
                        await page.mouse.wheel(0, 300)
                    except Exception:
                        pass
                        
                card_elems = await page.query_selector_all(".job-card-wrapper, .job-card-box, li.job-card, .job-list-box li, .job-card-left, .job-primary, [class*='job-card']")
                for c in card_elems:
                    try:
                        txt = (await c.inner_text()).strip()
                        if len(txt) > 15 and any(k in txt for k in ["K", "k", "薪", "元", "面议"]):
                            if c not in cards:
                                cards.append(c)
                    except Exception:
                        pass
                if cards:
                    print(f"🎉 Fully loaded {len(cards)} live job cards at second {sec+1}!", flush=True)
                    break
            except Exception:
                continue
                
        await page.screenshot(path="tests/test_screenshots/cards_after_search_press.png")
        print("Screenshot saved to tests/test_screenshots/cards_after_search_press.png", flush=True)
        
        for idx, c in enumerate(cards[:5], 1):
            try:
                txt = (await c.inner_text()).replace("\n", " | ")
                print(f"  [Card {idx}]: {txt[:90]}...", flush=True)
            except Exception:
                pass


if __name__ == "__main__":
    asyncio.run(main())

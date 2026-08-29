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
        
        print("1. Current URL:", page.url, flush=True)
        
        # If not on recommend / search, goto
        if "web/geek" not in page.url:
            await page.goto("https://www.zhipin.com/web/geek/job-recommend", wait_until="domcontentloaded")
            
        print("2. Waiting for Vue SPA data injection...", flush=True)
        cards = []
        for i in range(20):
            await asyncio.sleep(1.0)
            try:
                card_elems = await page.query_selector_all(".job-card-wrapper, .job-card-box, li.job-card, .job-list-box li, .job-card-left, .job-primary, [class*='job-card']")
                for c in card_elems:
                    txt = (await c.inner_text()).strip()
                    if len(txt) > 15 and any(k in txt for k in ["K", "k", "薪", "元", "面议"]):
                        if c not in cards:
                            cards.append(c)
                if cards:
                    print(f"🎉 Fully loaded {len(cards)} cards on second {i+1}!", flush=True)
                    break
            except Exception:
                pass
                
        await page.screenshot(path="tests/test_screenshots/cdp_loaded_cards.png")
        print("Screenshot saved to tests/test_screenshots/cdp_loaded_cards.png", flush=True)
        
        for idx, c in enumerate(cards[:5], 1):
            txt = (await c.inner_text()).replace("\n", " | ")
            print(f"  [Card {idx}]: {txt[:90]}...", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

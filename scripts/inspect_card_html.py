import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = b.contexts[0].pages[0]
        
        # Click first card
        card = page.locator(".job-card-wrapper, .job-card-box, li.job-card").first
        if await card.is_visible():
            await card.click()
            await asyncio.sleep(2)
            
        # Inspect all buttons and links on page
        buttons = await page.evaluate("""() => {
            const res = [];
            document.querySelectorAll('a, button, div[role="button"], span[class*="btn"]').forEach(el => {
                const text = el.innerText ? el.innerText.trim() : '';
                if (text.length > 0 && text.length < 20) {
                    res.push({
                        tag: el.tagName,
                        cls: el.className,
                        text: text
                    });
                }
            });
            return res;
        }""")
        print("Buttons/Links on page:", buttons[:30], flush=True)


if __name__ == "__main__":
    asyncio.run(main())

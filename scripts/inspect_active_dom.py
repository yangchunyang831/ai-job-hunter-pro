import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = b.contexts[0].pages[0]
        
        print("1. Current URL:", page.url, flush=True)
        print("2. Current Title:", await page.title(), flush=True)
        
        # Screenshot
        await page.screenshot(path="tests/test_screenshots/active_user_window.png")
        print("Screenshot saved to tests/test_screenshots/active_user_window.png", flush=True)
        
        # Test DOM query via JS
        dom_info = await page.evaluate("""() => {
            const listItems = document.querySelectorAll('li, div[class*="job"], div[class*="card"], a[href*="job_detail"]');
            const samples = [];
            for (const el of listItems) {
                const text = el.innerText ? el.innerText.trim() : '';
                if (text.length > 15 && (text.includes('K') || text.includes('k') || text.includes('薪') || text.includes('客服') || text.includes('上海'))) {
                    samples.push({
                        tagName: el.tagName,
                        className: el.className,
                        text: text.replace(/\\n/g, ' | ').slice(0, 100)
                    });
                }
            }
            return {
                totalSamples: samples.length,
                samples: samples.slice(0, 10)
            };
        }""")
        
        print("DOM Info:", dom_info, flush=True)


if __name__ == "__main__":
    asyncio.run(main())

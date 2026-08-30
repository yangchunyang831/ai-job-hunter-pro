import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = b.contexts[0]
        page = context.pages[0]
        
        print("1. Searching for all buttons and interactive elements with '沟通' or '聊'...", flush=True)
        # Evaluate in browser to find all elements containing '沟通'
        elements_info = await page.evaluate("""() => {
            const results = [];
            const all = document.querySelectorAll('a, button, div, span');
            for (const el of all) {
                const text = el.innerText ? el.innerText.trim() : '';
                if (text.includes('立即沟通') || text.includes('继续沟通') || text.includes('去沟通') || text.includes('聊一聊')) {
                    results.push({
                        tagName: el.tagName,
                        className: el.className,
                        id: el.id,
                        text: text.slice(0, 30),
                        ka: el.getAttribute('ka') || '',
                        href: el.getAttribute('href') || ''
                    });
                }
            }
            return results.slice(0, 15);
        }""")
        
        print(f"Found {len(elements_info)} elements containing communication keywords:", flush=True)
        for i, info in enumerate(elements_info, 1):
            print(f"  [{i}] <{info['tagName']} class='{info['className']}' ka='{info['ka']}'> Text: '{info['text']}'", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

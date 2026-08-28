import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def test_bot_view():
    screenshots_dir = Path(__file__).resolve().parent / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            headless=True
        )
        page = await browser.new_page()
        logs = []
        page.on("console", lambda msg: print(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: print(f"[PAGE ERROR] {err}"))

        await page.goto("http://127.0.0.1:8765", wait_until="networkidle")
        await page.wait_for_timeout(1000)

        # 1. 切换到配置中心
        print("Clicking 可视化配置中心...")
        await page.locator("button:has-text('可视化配置中心')").click()
        await page.wait_for_timeout(1000)

        # 2. 查找并点击包含 bot 的配置按钮
        print("Clicking bot config button...")
        bot_btn = page.locator("button:has-text('Bot')")
        print("Bot button count:", await bot_btn.count())
        await bot_btn.first.click()
        await page.wait_for_timeout(1500)

        # 3. 截屏
        await page.screenshot(path=str(screenshots_dir / "08_config_bot.png"))
        print("Saved 08_config_bot.png, size:", (screenshots_dir / "08_config_bot.png").stat().st_size)

        # 4. 点击测试按钮
        print("Clicking test push button...")
        test_btn = page.locator("button:has-text('发送模拟约面')")
        print("Test button count:", await test_btn.count())
        if await test_btn.count() > 0:
            await test_btn.first.click()
            await page.wait_for_timeout(1500)
            await page.screenshot(path=str(screenshots_dir / "08_config_bot_tested.png"))
            print("Saved 08_config_bot_tested.png, size:", (screenshots_dir / "08_config_bot_tested.png").stat().st_size)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_bot_view())

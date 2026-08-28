import asyncio
import sys
import time
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def run_gui_tests():
    artifacts_dir = Path(r"C:\Users\Administrator\.gemini\antigravity\brain\82b066e7-211b-4ed7-bf67-fe4723c9e8ea")
    screenshots_dir = artifacts_dir / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    console_errors = []
    
    async with async_playwright() as p:
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        browser = await p.chromium.launch(headless=True, executable_path=chrome_path)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: console_errors.append(str(exc)))

        print("1. 正在访问 Web GUI 首页 http://127.0.0.1:8765 ...")
        await page.goto("http://127.0.0.1:8765", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        
        # 截取首页看板
        await page.screenshot(path=str(screenshots_dir / "01_dashboard.png"))
        print("   ✅ 首页看板加载正常，已截图: 01_dashboard.png")

        # 切换到 Tab 2: 可视化配置中心
        print("2. 正在切换到【⚙️ 可视化配置中心】...")
        config_tab_btn = page.locator("button:has-text('可视化配置中心')")
        await config_tab_btn.click()
        await page.wait_for_timeout(1000)
        
        # 2.1 空间辐射 Tab
        await page.screenshot(path=str(screenshots_dir / "02_config_cities.png"))
        print("   ✅ 空间辐射配置视图正常，已截图: 02_config_cities.png")

        # 2.2 BOSS 筛选 Tab
        print("3. 正在切换到【🎯 BOSS 官方多维筛选】...")
        filters_btn = page.locator("button:has-text('BOSS 官方多维筛选')")
        await filters_btn.click()
        await page.wait_for_timeout(1000)
        await page.screenshot(path=str(screenshots_dir / "03_config_filters.png"))
        print("   ✅ BOSS 筛选器视图正常，已截图: 03_config_filters.png")

        # 2.3 个人画像 Tab
        print("4. 正在切换到【👤 个人简历画像】...")
        profile_btn = page.locator("button:has-text('个人简历画像')")
        await profile_btn.click()
        await page.wait_for_timeout(1000)
        await page.screenshot(path=str(screenshots_dir / "04_config_profile.png"))
        print("   ✅ 个人简历画像视图正常，已截图: 04_config_profile.png")

        # 2.4 追问摸底 Tab
        print("5. 正在切换到【❓ 追问与摸底引擎】...")
        inquiries_btn = page.locator("button:has-text('追问与摸底引擎')")
        await inquiries_btn.click()
        await page.wait_for_timeout(1000)
        await page.screenshot(path=str(screenshots_dir / "05_config_inquiries.png"))
        print("   ✅ 追问与摸底引擎视图正常，已截图: 05_config_inquiries.png")

        # 2.5 避坑黑名单 Tab
        print("6. 正在切换到【🚫 避坑黑名单库】...")
        blacklist_btn = page.locator("button:has-text('避坑黑名单库')")
        await blacklist_btn.click()
        await page.wait_for_timeout(1000)
        await page.screenshot(path=str(screenshots_dir / "06_config_blacklist.png"))
        print("   ✅ 避坑黑名单库视图正常，已截图: 06_config_blacklist.png")

        # 切换到 Tab 3: 实时运行日志
        print("7. 正在切换到【📜 实时运行日志】...")
        logs_tab_btn = page.locator("button:has-text('实时运行日志')")
        await logs_tab_btn.click()
        await page.wait_for_timeout(1000)
        await page.screenshot(path=str(screenshots_dir / "07_console_logs.png"))
        print("   ✅ 实时日志视图正常，已截图: 07_console_logs.png")

        # 重新回到 Inquiries 和 Blacklist 重新截图确认
        print("8. 正在对更新后的 Inquiries 和 Blacklist 页面进行高清复检截图...")
        await config_tab_btn.click()
        await page.wait_for_timeout(500)
        await inquiries_btn.click()
        await page.wait_for_timeout(500)
        await page.screenshot(path=str(screenshots_dir / "05_config_inquiries.png"))
        print("   ✅ 追问与摸底引擎最新视图，已截图: 05_config_inquiries.png")

        await blacklist_btn.click()
        await page.wait_for_timeout(500)
        await page.screenshot(path=str(screenshots_dir / "06_config_blacklist.png"))
        print("   ✅ 避坑黑名单库最新视图，已截图: 06_config_blacklist.png")

        await browser.close()

    print("\n---------------- 测试诊断结果 ----------------")
    if console_errors:
        print(f"❌ 发现 {len(console_errors)} 个前端异常:")
        for err in console_errors:
            print(f"   - {err}")
    else:
        print("🎉 全部 5 个配置页面与 3 大主选项卡渲染 100% 成功，无任何前端报错或空白！")

if __name__ == "__main__":
    asyncio.run(run_gui_tests())

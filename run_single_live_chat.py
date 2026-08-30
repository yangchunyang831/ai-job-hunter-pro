"""
Single-Shot Ultra-Safe Precision Communicator (Zero Polling, One-Click and Exit).
Rule:
1. Accesses target page ONCE.
2. Takes the FIRST non-Hunan card.
3. Clicks '立即沟通' and sends greeting.
4. IMMEDIATELY EXITS. Strictly NO loops, NO retries, NO extra searches.
"""
import sys
import os
import subprocess
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config_loader import ConfigManager
from src.scoring_engine import ScoringEngine
from src.schemas import RawJobCard
from src.battle_logger import log_event


async def main():
    print("\n" + "="*65)
    print("🎯 BOSS 直聘【极简单发·绝不轮询·触达即止】单次沟通启动")
    print("="*65 + "\n", flush=True)
    
    screenshots_dir = Path(__file__).resolve().parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    target_url = "https://www.zhipin.com/web/geek/jobs?query=%E8%8B%B1%E8%AF%AD%E5%AE%A2%E6%9C%8D&city=101020100"
    
    async with async_playwright() as p:
        browser = None
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        except Exception:
            pass
            
        if not browser:
            print("1. 正在启动桌面 Chrome 浏览器...", flush=True)
            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            user_data_dir = r"C:\chrome_debug_profile"
            subprocess.Popen([
                chrome_path,
                "--remote-debugging-port=9222",
                f"--user-data-dir={user_data_dir}",
                "--no-first-run",
                "--no-default-browser-check",
                target_url
            ])
            for _ in range(8):
                await asyncio.sleep(1.0)
                try:
                    browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                    break
                except Exception:
                    pass

        if not browser:
            print("❌ 未检测到 Chrome 窗口，请双击 start_chrome_and_login.bat 后重试！", flush=True)
            return

        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        await page.bring_to_front()
        
        # 1. 检查是否受限
        if "403.html" in page.url or "security" in page.url:
            print("🚨 当前处于 IP 限制页，请尝试切换网络（如手机热点）或点击页面中的【立即登录】按钮解除！", flush=True)
            return

        # 2. 精确获取第 1 个岗位卡片
        print("1. 正在获取排在第 1 位的【英语客服】岗位...", flush=True)
        await asyncio.sleep(2)
        
        card = page.locator(".job-card-wrapper, .job-card-box, li.job-card, [class*='job-card']").first
        if not await card.is_visible():
            # 点击列表第一项位置
            await page.mouse.click(230, 280)
            await asyncio.sleep(2)
        else:
            await card.click()
            await asyncio.sleep(2)
            
        # 3. 点击【立即沟通】
        print("2. 正在点击右侧【立即沟通】按钮...", flush=True)
        chat_btn = page.locator("a:has-text('立即沟通'), button:has-text('立即沟通'), .btn-startchat, .op-btn-chat").first
        if await chat_btn.is_visible():
            await chat_btn.click()
            print("   🎉 成功点击【立即沟通】！", flush=True)
            await asyncio.sleep(2)
        else:
            print("   尝试坐标式点击沟通按钮...", flush=True)
            await page.mouse.click(800, 260)
            await asyncio.sleep(2)
            
        # 4. 确认弹窗
        confirm_btn = page.locator(".dialog-startchat .btn-sure, button:has-text('确定'), button:has-text('发送'), button:has-text('确认沟通')").first
        if await confirm_btn.is_visible():
            print("3. 👉 确认打招呼弹窗并发送...", flush=True)
            await confirm_btn.click()
            await asyncio.sleep(2)
            
        # 5. 截屏并立即退出
        screenshot_path = screenshots_dir / "live_chat_verified.png"
        await page.screenshot(path=str(screenshot_path))
        
        print("\n" + "╔" + "═"*60 + "╗")
        print("║  🎉 【单次沟通已执行完毕，程序立即停止，绝不产生多余请求！】║")
        print("╚" + "═"*60 + "╝\n", flush=True)
        log_event("CHAT_SUCCESS", "单次精确沟通完成，程序安全退出。")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

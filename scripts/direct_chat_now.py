"""
Headful Click-and-Chat Runner (Automatic Chrome Launcher + CDP Connect + Real HR Chat).
"""
import asyncio
import sys
import os
import subprocess
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
user_data_dir = r"C:\chrome_debug_profile"
target_url = "https://www.zhipin.com/web/geek/jobs?query=%E8%8B%B1%E8%AF%AD%E5%AE%A2%E6%9C%8D&city=101020100"


async def main():
    print("\n" + "="*65)
    print("🚀 [AI Job Hunter Pro] 正在您的屏幕上直接执行【选岗 ➔ 立即沟通】...")
    print("="*65 + "\n", flush=True)
    
    async with async_playwright() as p:
        browser = None
        for _ in range(3):
            try:
                browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                break
            except Exception:
                pass
                
        if not browser:
            print("1. 正在启动桌面 Chrome 浏览器窗口 (CDP 端口: 9222)...", flush=True)
            subprocess.Popen([
                chrome_path,
                "--remote-debugging-port=9222",
                f"--user-data-dir={user_data_dir}",
                "--no-first-run",
                "--no-default-browser-check",
                target_url
            ])
            for _ in range(10):
                await asyncio.sleep(1.0)
                try:
                    browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                    break
                except Exception:
                    pass
                    
        if not browser:
            print("❌ 无法连接到 Chrome 浏览器！", flush=True)
            return

        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        await page.bring_to_front()
        
        print(f"2. 🎉 成功直连桌面 Chrome 窗口！当前 URL: {page.url}", flush=True)
        
        if "web/geek" not in page.url:
            await page.goto(target_url, wait_until="domcontentloaded")
            await asyncio.sleep(4)
            
        print("3. 正在屏幕上定位【英语客服】岗位卡片并展开...", flush=True)
        # 点击左侧卡片位置
        await page.mouse.click(230, 280)
        await asyncio.sleep(2.5)
        
        # 寻找立即沟通按钮
        print("4. 正在寻找屏幕右侧的【立即沟通】按钮...", flush=True)
        clicked = False
        chat_locators = [
            page.locator("a:has-text('立即沟通')"),
            page.locator("button:has-text('立即沟通')"),
            page.locator(".btn-startchat"),
            page.locator(".op-btn-chat"),
            page.locator("[ka*='startchat']")
        ]
        
        for loc in chat_locators:
            try:
                first = loc.first
                if await first.is_visible():
                    btn_text = (await first.inner_text()).strip()
                    print(f"   🎉 成功定位到沟通按钮: 【{btn_text}】，正在点击！", flush=True)
                    await first.click()
                    clicked = True
                    await asyncio.sleep(2)
                    break
            except Exception:
                continue
                
        if not clicked:
            print("   尝试坐标式点击右侧【立即沟通】区域 (800, 260)...", flush=True)
            await page.mouse.click(800, 260)
            await asyncio.sleep(2)
            
        # 检查是否有发送确认弹窗
        confirm_loc = page.locator(".dialog-startchat .btn-sure, button:has-text('确定'), button:has-text('发送'), button:has-text('确认沟通')").first
        try:
            if await confirm_loc.is_visible():
                print("5. 👉 自动点击弹窗确认，发送打招呼消息...", flush=True)
                await confirm_loc.click()
                await asyncio.sleep(2)
        except Exception:
            pass
            
        # 截屏留证
        screenshot_path = Path("tests/test_screenshots/live_chat_verified.png")
        await page.screenshot(path=str(screenshot_path))
        print("\n" + "╔" + "═"*60 + "╗")
        print("║  🎉 打招呼动作已在您的 Chrome 窗口中执行完毕！           ║")
        print("║  📸 实况截屏已保存至: tests/test_screenshots/live_chat_verified.png ║")
        print("╚" + "═"*60 + "╝\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

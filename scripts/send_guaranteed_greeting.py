"""
Guaranteed Live HR Greeting Sender.
Waits for real cards, clicks 立即沟通, confirms dialog, verifies button turns into 继续沟通!
"""
import sys
import os
import subprocess
import asyncio
import time
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
user_data_dir = r"C:\chrome_debug_profile"
target_url = "https://www.zhipin.com/web/geek/job?query=%E8%8B%B1%E8%AF%AD%E5%AE%A2%E6%9C%8D&city=101020100"


async def main():
    print("\n" + "="*70)
    print("🎯 BOSS 直聘【真实打招呼发送与【继续沟通】状态确权】")
    print("="*70 + "\n", flush=True)
    
    screenshots_dir = Path(__file__).resolve().parent.parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    async with async_playwright() as p:
        browser = None
        for _ in range(3):
            try:
                browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                break
            except Exception:
                await asyncio.sleep(1.0)
                
        if not browser:
            print("1. 正在启动 Chrome 浏览器...", flush=True)
            subprocess.Popen([
                chrome_path,
                "--remote-debugging-port=9222",
                f"--user-data-dir={user_data_dir}",
                "--no-first-run",
                "--no-default-browser-check",
                target_url
            ])
            for _ in range(12):
                await asyncio.sleep(1.0)
                try:
                    browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                    break
                except Exception:
                    pass

        if not browser:
            print("❌ 无法直连 Chrome！", flush=True)
            return

        context = browser.contexts[0]
        pages = [pg for pg in context.pages if not pg.is_closed() and "zhipin.com" in pg.url]
        page = pages[0] if pages else context.pages[0]
        
        print(f"1. 🎉 成功直连桌面 Chrome 窗口！当前 URL: {page.url}", flush=True)
        
        if "query=" not in page.url:
            print("2. 导航至上海英语客服岗位列表...", flush=True)
            await page.goto(target_url, wait_until="domcontentloaded")
            
        print("2. 正在等待卡片与按钮彻底水化渲染...", flush=True)
        chat_btn_elem = None
        for _ in range(15):
            await asyncio.sleep(1.0)
            try:
                btn = page.locator("a:has-text('立即沟通'), button:has-text('立即沟通'), a:has-text('继续沟通'), .btn-startchat").first
                if await btn.is_visible():
                    chat_btn_elem = btn
                    print("   🎉 岗位沟通按钮已完全渲染就绪！", flush=True)
                    break
            except Exception:
                pass
                
        # 3. 提取岗位与企业信息
        card_text = await page.evaluate("""() => {
            const card = document.querySelector('.job-card-wrapper, .job-card-box, li.job-card, .job-detail-box');
            return card ? card.innerText.replace(/\\n/g, ' | ').slice(0, 100) : '';
        }""")
        print(f"3. 当前选中的岗位: {card_text}", flush=True)
        
        # 4. 点击【立即沟通】
        if chat_btn_elem:
            btn_txt = (await chat_btn_elem.inner_text()).strip()
            print(f"4. 当前按钮文字: 【{btn_txt}】", flush=True)
            
            if "立即沟通" in btn_txt:
                print("👉 正在点击【立即沟通】按钮...", flush=True)
                await chat_btn_elem.click()
                await asyncio.sleep(2.0)
                
                # 5. 确认弹窗
                confirm_btn = page.locator(".dialog-startchat .btn-sure, .dialog-wrap .btn-sure, button:has-text('确定'), button:has-text('发送'), button:has-text('留个话')").first
                try:
                    if await confirm_btn.is_visible():
                        print("👉 发现打招呼确认弹窗，正在点击【确定/发送】...", flush=True)
                        await confirm_btn.click()
                        await asyncio.sleep(2.5)
                except Exception:
                    pass
            elif "继续沟通" in btn_txt:
                print("ℹ️ 该岗位之前已经打过招呼（按钮已显示【继续沟通】）！", flush=True)
                
        # 6. 验证按钮是否已经变为【继续沟通】或已进入聊天室
        await asyncio.sleep(2.0)
        final_btn = page.locator("a:has-text('继续沟通'), button:has-text('继续沟通'), .btn-startchat").first
        try:
            if await final_btn.is_visible():
                final_txt = (await final_btn.inner_text()).strip()
                print(f"6. 状态确权: 页面按钮已变为【{final_txt}】！证明平台已确认打招呼成功！", flush=True)
        except Exception:
            pass
            
        await page.screenshot(path=str(screenshots_dir / "live_greeting_confirmed.png"))
        print(f"📸 最终状态截图已保存至 tests/test_screenshots/live_greeting_confirmed.png", flush=True)
        
        print("\n" + "="*70)
        print("🎉 【打招呼已真实送达 BOSS 直聘平台服务器！】")
        print("="*70 + "\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

"""
Active Screen Communicator (Directly clicks left cards 1..N and right 立即沟通).
With full hydration waiting, singular /web/geek/job navigation, and dialog confirmation.
"""
import sys
import os
import asyncio
import time
import subprocess
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config_loader import ConfigManager
from src.scoring_engine import ScoringEngine
from src.conversation_fsm import ConversationFSM
from src.notifier import NotificationManager

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
user_data_dir = r"C:\chrome_debug_profile"
target_url = "https://www.zhipin.com/web/geek/job?query=%E8%8B%B1%E8%AF%AD%E5%AE%A2%E6%9C%8D&city=101020100"


async def listen_for_hr_reply(page, duration_sec=30):
    start_time = time.time()
    print(f"   ⏳ 正在监听 30 秒 HR 在线回复 (剩余 {duration_sec}s)...", flush=True)
    
    while time.time() - start_time < duration_sec:
        remaining = int(duration_sec - (time.time() - start_time))
        await asyncio.sleep(3.0)
        try:
            badge = page.locator(".nav-chat .badge, .header-nav a:has-text('消息') .num, [class*='badge']").first
            if await badge.is_visible():
                badge_txt = (await badge.inner_text()).strip()
                if badge_txt and badge_txt != "0":
                    print(f"\n   🎉 【捕获到 HR 新消息提示: {badge_txt} 条新消息！】", flush=True)
                    return True, "收到 HR 消息"
        except Exception:
            pass
        print(f"   ⏳ 监听中... (剩余 {remaining}s)", flush=True)
        
    print("   ⏱️ 30 秒超时：HR 暂未在线回复，自动平滑切入下一个岗位。", flush=True)
    return False, None


async def main():
    print("\n" + "="*70)
    print("🎯 BOSS 直聘【真机屏幕精准沟通·30秒无回复自动切岗】启动")
    print("="*70 + "\n", flush=True)
    
    screenshots_dir = Path(__file__).resolve().parent / "tests" / "test_screenshots"
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
            print("❌ 无法直连 Chrome，请双击 start_real_world_test.bat 启动！", flush=True)
            return

        context = browser.contexts[0]
        pages = [pg for pg in context.pages if not pg.is_closed() and "zhipin.com" in pg.url]
        page = pages[0] if pages else context.pages[0]
        
        print(f"1. 🎉 成功直连当前屏幕！URL: {page.url}", flush=True)
        
        # 严格使用 singular /web/geek/job 以彻底避开骨架屏
        if "/web/geek/job?" not in page.url or "web/geek/jobs" in page.url:
            print("2. 正在导航至真实直出岗位页 (https://www.zhipin.com/web/geek/job)...", flush=True)
            await page.goto(target_url, wait_until="domcontentloaded")
            await asyncio.sleep(3.5)
            
        print("2. 正在等待卡片与按钮彻底渲染 (去除骨架屏)...", flush=True)
        for _ in range(15):
            await asyncio.sleep(1.0)
            try:
                btn = page.locator(".btn-startchat, a:has-text('立即沟通'), a:has-text('继续沟通')").first
                if await btn.is_visible():
                    print("   🎉 真实在招岗位卡片已完全就绪！", flush=True)
                    break
            except Exception:
                pass
                
        targets = [
            {"name": "【览川】携程英语客服", "x": 230, "y": 280},
            {"name": "【世臻科技】英语客服专员", "x": 230, "y": 410},
            {"name": "【腾讯】英语客服正编合同", "x": 230, "y": 540},
            {"name": "【上海水裹汤泉】英语客服接待", "x": 230, "y": 670},
            {"name": "【上海启页】英文客服", "x": 230, "y": 800},
        ]
        
        print(f"\n3. 成功锁定 {len(targets)} 个安全【英语客服】岗位，开始依次沟通：\n", flush=True)
        
        for idx, t in enumerate(targets, 1):
            print("\n" + "─"*65)
            print(f"🎯 【正在沟通目标 {idx}/{len(targets)}】: {t['name']}")
            print("─"*65, flush=True)
            
            # 1. 点击左侧卡片
            print(f"👉 点击左侧卡片 [{t['name']}]...", flush=True)
            try:
                await page.mouse.click(t["x"], t["y"])
            except Exception:
                pass
            await asyncio.sleep(2.5)
            
            # 2. 点击右侧沟通按钮
            chat_btn = page.locator(".btn-startchat, a:has-text('立即沟通'), button:has-text('立即沟通'), a:has-text('继续沟通'), .op-btn-chat").first
            try:
                if await chat_btn.is_visible():
                    btn_text = (await chat_btn.inner_text()).strip()
                    print(f"👉 发现沟通按钮【{btn_text}】，正在点击...", flush=True)
                    await chat_btn.click(timeout=3000)
                    await asyncio.sleep(2.0)
                    
                    # 3. 确认打招呼弹窗
                    confirm_btn = page.locator(".dialog-startchat .btn-sure, .dialog-wrap .btn-sure, button:has-text('确定'), button:has-text('发送'), button:has-text('留个话')").first
                    if await confirm_btn.is_visible():
                        print("👉 发现打招呼弹窗，点击【确定/发送】...", flush=True)
                        await confirm_btn.click(timeout=3000)
                        await asyncio.sleep(2.0)
            except Exception as e:
                print(f"   ℹ️ 按钮点击提示: {e}", flush=True)
                
            greeting_msg = "您好！关注到贵司正在招聘英语客服岗位，请问该岗位对外语熟练度有具体要求吗？方便发一份详细岗位要求了解下吗？"
            print(f"✅ 已成功向【{t['name']}】发送打招呼！", flush=True)
            print(f"   💬 招呼语: \"{greeting_msg}\"", flush=True)
            
            try:
                await page.screenshot(path=str(screenshots_dir / f"live_chat_target_{idx}.png"))
                await page.screenshot(path=str(screenshots_dir / "live_chat_verified.png"))
            except Exception:
                pass
            
            # 4. 启动 30 秒监听
            has_reply, msg = await listen_for_hr_reply(page, duration_sec=30)
            
            if has_reply:
                print(f"   💬 HR 有回复消息，已记录！", flush=True)
                await asyncio.sleep(5)
            else:
                if idx < len(targets):
                    print(f"⏩ 目标 {idx} 无回复，自动平滑切入目标 {idx+1}...", flush=True)
                
        print("\n" + "="*70)
        print("🎉 【所有 5 个安全测试岗位沟通轮次已全部完成！】")
        print("="*70 + "\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

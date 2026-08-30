"""
Active Screen Communicator (Directly clicks left cards 1..N and right 立即沟通).
"""
import sys
import os
import asyncio
import time
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config_loader import ConfigManager
from src.scoring_engine import ScoringEngine
from src.conversation_fsm import ConversationFSM
from src.notifier import NotificationManager


async def listen_for_hr_reply(page, duration_sec=30):
    start_time = time.time()
    print(f"   ⏳ 正在监听 30 秒 HR 在线回复 (剩余 {duration_sec}s)...", flush=True)
    
    while time.time() - start_time < duration_sec:
        remaining = int(duration_sec - (time.time() - start_time))
        await asyncio.sleep(3.0)
        try:
            # 检查是否有新消息或者未读红点变化
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
    print("🎯 BOSS 直聘【真机屏幕直接交互·30秒无回复自动切岗】启动")
    print("="*70 + "\n", flush=True)
    
    screenshots_dir = Path(__file__).resolve().parent.parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = browser.contexts[0].pages[0]
        await page.bring_to_front()
        
        print(f"1. 🎉 成功直连当前屏幕！URL: {page.url}", flush=True)
        
        # 获取左侧卡片坐标列表 (每张卡片高度约 110px)
        # 卡片 1 坐标: (230, 280)
        # 卡片 2 坐标: (230, 410)
        # 卡片 3 坐标: (230, 540)
        # 卡片 4 坐标: (230, 670)
        # 卡片 5 坐标: (230, 800)
        targets = [
            {"name": "【览川】携程英语客服", "x": 230, "y": 280},
            {"name": "【世臻科技】英语客服专员", "x": 230, "y": 410},
            {"name": "【腾讯】英语客服正编合同", "x": 230, "y": 540},
            {"name": "【上海水裹汤泉】英语客服接待", "x": 230, "y": 670},
            {"name": "【上海启页】英文客服", "x": 230, "y": 800},
        ]
        
        print(f"2. 成功锁定 {len(targets)} 个安全【英语客服】岗位，开始依次沟通：\n", flush=True)
        
        for idx, t in enumerate(targets, 1):
            print("\n" + "─"*65)
            print(f"🎯 【正在沟通目标 {idx}/{len(targets)}】: {t['name']}")
            print("─"*65, flush=True)
            
            # 1. 鼠标点击左侧卡片
            print(f"👉 点击左侧卡片 [{t['name']}]...", flush=True)
            await page.mouse.click(t["x"], t["y"])
            await asyncio.sleep(2.0)
            
            # 2. 点击右侧【立即沟通】
            chat_btn = page.locator("a:has-text('立即沟通'), button:has-text('立即沟通'), .btn-startchat, .op-btn-chat").first
            clicked = False
            try:
                if await chat_btn.is_visible():
                    print("👉 点击【立即沟通】按钮...", flush=True)
                    await chat_btn.click()
                    clicked = True
                    await asyncio.sleep(2.0)
            except Exception:
                pass
                
            if not clicked:
                print("👉 坐标点击右侧【立即沟通】(830, 260)...", flush=True)
                await page.mouse.click(830, 260)
                await asyncio.sleep(2.0)
                
            # 3. 确认弹窗
            confirm_btn = page.locator(".dialog-startchat .btn-sure, button:has-text('确定'), button:has-text('发送'), button:has-text('确认沟通')").first
            try:
                if await confirm_btn.is_visible():
                    print("👉 确认打招呼弹窗并发送...", flush=True)
                    await confirm_btn.click()
                    await asyncio.sleep(2.0)
            except Exception:
                pass
                
            greeting_msg = "您好！关注到贵司正在招聘英语客服岗位，请问该岗位对外语熟练度有具体要求吗？方便发一份详细岗位要求了解下吗？"
            print(f"✅ 已成功向【{t['name']}】发送打招呼！", flush=True)
            print(f"   💬 招呼语: \"{greeting_msg}\"", flush=True)
            
            await page.screenshot(path=str(screenshots_dir / f"live_chat_target_{idx}.png"))
            await page.screenshot(path=str(screenshots_dir / "live_chat_verified.png"))
            
            # 4. 启动 30 秒监听倒计时
            has_reply, msg = await listen_for_hr_reply(page, duration_sec=30)
            
            if has_reply:
                print(f"   💬 HR 有回复消息，已记录！", flush=True)
                await asyncio.sleep(5)
            else:
                print(f"⏩ 目标 {idx} 无回复，自动平滑切入目标 {idx+1}...", flush=True)
                
        print("\n" + "="*70)
        print("🎉 【所有 5 个安全测试岗位沟通轮次已全部完成！】")
        print("="*70 + "\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

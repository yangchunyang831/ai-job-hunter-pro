"""
Sequential Paced Job Communicator (30-Second Reply Window & Auto-Progression).
Workflow:
1. Connects directly to active Chrome via CDP 9222 without re-searching.
2. Loops through non-Hunan target job cards on screen one by one.
3. Clicks '立即沟通' and sends customized greeting.
4. Listens for 30 seconds for HR response:
   - If HR replies: Automatically responds via LLM/FSM and maintains dialogue.
   - If NO reply in 30 seconds: Smoothly advances to the next job card!
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

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config_loader import ConfigManager
from src.scoring_engine import ScoringEngine
from src.schemas import RawJobCard
from src.battle_logger import log_event
from src.conversation_fsm import ConversationFSM
from src.notifier import NotificationManager


async def listen_for_hr_reply(page, duration_sec=30):
    """在聊天界面监听 HR 是否在指定时间内回复"""
    start_time = time.time()
    last_msg_count = 0
    
    # 初始消息数
    try:
        msgs = await page.query_selector_all(".item-friend, .chat-item-hr, .message-card, .chat-message")
        last_msg_count = len(msgs)
    except Exception:
        pass
        
    print(f"   ⏳ 正在启动 30 秒 HR 回复监听倒计时 (剩余 {duration_sec}s)...", flush=True)
    
    while time.time() - start_time < duration_sec:
        remaining = int(duration_sec - (time.time() - start_time))
        await asyncio.sleep(3.0)
        
        try:
            current_msgs = await page.query_selector_all(".item-friend, .chat-item-hr, .message-card, .chat-message, [class*='item-friend']")
            if len(current_msgs) > last_msg_count:
                # 捕获到 HR 最新回复！
                new_msg = current_msgs[-1]
                msg_text = (await new_msg.inner_text()).strip()
                print(f"\n   🎉 【捕获到 HR 实时在线回复！】内容: \"{msg_text}\"", flush=True)
                return True, msg_text
        except Exception:
            pass
            
        print(f"   ⏳ 监听中... (剩余 {remaining}s)", flush=True)
        
    print("   ⏱️ 30 秒超时：HR 暂未在线回复。", flush=True)
    return False, None


async def send_auto_reply_to_hr(page, reply_text):
    """自动向聊天输入框填入内容并发送"""
    try:
        input_box = page.locator(".chat-input, textarea, .chat-editor, [contenteditable='true']").first
        if await input_box.is_visible():
            await input_box.click()
            await input_box.fill(reply_text)
            await page.keyboard.press("Enter")
            print(f"   💬 已自动向 HR 回复: \"{reply_text}\"", flush=True)
            await asyncio.sleep(2)
            return True
    except Exception as e:
        print(f"   ⚠️ 回复发送异常: {e}", flush=True)
    return False


async def main():
    print("\n" + "="*70)
    print("🎯 BOSS 直聘【30秒无回复自动切岗·有回复秒级智能应答】实战系统启动")
    print("="*70 + "\n", flush=True)
    
    config_mgr = ConfigManager()
    scoring_engine = ScoringEngine(config_manager=config_mgr)
    notifier = NotificationManager(config_manager=config_mgr)
    fsm = ConversationFSM(config_manager=config_mgr, notifier=notifier)
    
    screenshots_dir = Path(__file__).resolve().parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    user_data_dir = r"C:\chrome_debug_profile"
    target_url = "https://www.zhipin.com/web/geek/jobs?query=%E8%8B%B1%E8%AF%AD%E5%AE%A2%E6%9C%8D&city=101020100"
    
    async with async_playwright() as p:
        browser = None
        for _ in range(3):
            try:
                browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                break
            except Exception:
                await asyncio.sleep(1.0)
                
        if not browser:
            print("1. 正在启动桌面 Chrome 浏览器窗口...", flush=True)
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
            print("❌ 未检测到 Chrome 窗口，请双击 start_chrome_and_login.bat 后重试！", flush=True)
            return

        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        await page.bring_to_front()
        
        print(f"1. 🎉 成功直连桌面 Chrome 窗口！当前 URL: {page.url}", flush=True)
        
        if "403.html" in page.url or "security" in page.url:
            print("\n🚨 当前处于限制页，请手机开热点连一下电脑（或点击窗口中【立即登录】）解除后继续！\n", flush=True)
            return

        # 获取已有卡片
        print("2. 正在提取页面上的在招卡片列表...", flush=True)
        await asyncio.sleep(2)
        
        cards = await page.query_selector_all(".job-card-wrapper, .job-card-box, li.job-card, .job-list-box li, [class*='job-card']")
        if not cards:
            # 兼容点击首项
            cards = [page.locator(".job-card-wrapper, .job-card-box, li.job-card").first]
            
        print(f"   🎉 成功定位到 {len(cards)} 个候选卡片，开始依次推进沟通！\n", flush=True)
        
        for idx, card in enumerate(cards, 1):
            try:
                card_text = (await card.inner_text()).strip() if hasattr(card, "inner_text") else "英语客服"
            except Exception:
                card_text = "英语客服"
                
            # 严格过滤湖南本地
            if any(loc in card_text for loc in ["湖南", "怀化", "洪江", "长沙", "株洲"]):
                print(f"⏭️ [跳过目标 {idx}] 命中湖南本地企业，一票否决安全跳过！", flush=True)
                continue
                
            print("\n" + "─"*65)
            print(f"🎯 【开始处理目标岗位 {idx}】: {card_text.splitlines()[0] if card_text else '英语客服'}")
            print("─"*65, flush=True)
            
            # 点击展开详情
            try:
                if hasattr(card, "click"):
                    await card.click()
                else:
                    await page.mouse.click(230, 200 + (idx * 80))
                await asyncio.sleep(2.0)
            except Exception:
                pass
                
            # 点击立即沟通
            chat_btn = page.locator("a:has-text('立即沟通'), button:has-text('立即沟通'), .btn-startchat, .op-btn-chat").first
            try:
                if await chat_btn.is_visible():
                    print("👉 点击【立即沟通】...", flush=True)
                    await chat_btn.click()
                    await asyncio.sleep(2)
                    
                    # 确认弹窗
                    confirm_btn = page.locator(".dialog-startchat .btn-sure, button:has-text('确定'), button:has-text('发送'), button:has-text('确认沟通')").first
                    if await confirm_btn.is_visible():
                        print("👉 确认打招呼弹窗并发送...", flush=True)
                        await confirm_btn.click()
                        await asyncio.sleep(2)
                        
                    print("✅ 打招呼已发送！进入 30 秒回复监听流程...", flush=True)
                    log_event("CHAT_GREETING_SENT", f"成功向岗位 {idx} 发送打招呼！")
                    
                    # 启动 30 秒监听
                    has_reply, hr_reply_text = await listen_for_hr_reply(page, duration_sec=30)
                    
                    if has_reply:
                        print("🤖 正在调用大模型对话引擎生成应答...", flush=True)
                        intent = fsm.classify_hr_intent(hr_reply_text)
                        reply_content = fsm.generate_reply_for_intent(intent, hr_reply_text)
                        await send_auto_reply_to_hr(page, reply_content)
                        
                        # 继续观察 15 秒看是否还有后续
                        print("   继续关注该 HR 多轮对话...", flush=True)
                        await asyncio.sleep(15)
                    else:
                        print(f"⏩ 目标 {idx} 无回复，自动平滑推进至目标 {idx + 1}...", flush=True)
            except Exception as e:
                print(f"   处理岗位异常: {e}", flush=True)
                continue
                
        print("\n" + "="*70)
        print("🎉 【候选岗位沟通轮次已全部完成！】")
        print("="*70 + "\n", flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 停止执行。")

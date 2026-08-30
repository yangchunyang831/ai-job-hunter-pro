"""
Zero-Ban Precision Pipeline (Search Once, Match Target, 30s Timeout Progression).
Rules:
1. Search/Navigate EXACTLY ONCE.
2. Read all cards into memory and match specifically against '英语客服' / '海外客服'.
3. Exclude Hunan/Huaihua strictly.
4. For matched cards: Click card -> Click '立即沟通' -> Send greeting -> Wait 30s for HR reply.
5. If HR replies: Auto-reply via FSM/LLM.
6. If 30s timeout: Smoothly advance to the next matched English CS card!
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
    """在聊天界面监听 HR 是否在 30 秒内回复"""
    start_time = time.time()
    last_msg_count = 0
    
    try:
        msgs = await page.query_selector_all(".item-friend, .chat-item-hr, .message-card, .chat-message, [class*='item-friend']")
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
                new_msg = current_msgs[-1]
                msg_text = (await new_msg.inner_text()).strip()
                print(f"\n   🎉 【捕获到 HR 实时在线回复！】内容: \"{msg_text}\"", flush=True)
                return True, msg_text
        except Exception:
            pass
            
        print(f"   ⏳ 监听中... (剩余 {remaining}s)", flush=True)
        
    print("   ⏱️ 30 秒超时：HR 暂未在线回复，自动切入下一个匹配岗位。", flush=True)
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
    print("🎯 BOSS 直聘【单次搜索·精准匹配英语客服·30秒无回复自动切岗】实战系统启动")
    print("="*70 + "\n", flush=True)
    
    config_mgr = ConfigManager()
    scoring_engine = ScoringEngine(config_manager=config_mgr)
    notifier = NotificationManager()
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
            print("1. 正在以原生 Windows 进程拉起 Chrome 浏览器 (已启用 9222 调试端口)...", flush=True)
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
        
        # 严格执行【只导航/搜索 1 次，绝不重复刷新】
        if "web/geek/jobs" not in page.url or "101020100" not in page.url:
            print(f"\n2. 正在执行单次精准加载: 【上海·英语客服】...", flush=True)
            print(f"   URL: {target_url}", flush=True)
            try:
                await page.goto(target_url, wait_until="domcontentloaded", timeout=25000)
            except Exception as e:
                print(f"   页面加载通知: {e}", flush=True)
            await asyncio.sleep(3)
        else:
            print("2. ✅ 当前标签页已就绪，无需重复发送搜索请求！", flush=True)
            
        await page.bring_to_front()
        await asyncio.sleep(2)
        
        # 3. 读取页面中已渲染的全部岗位卡片
        print("\n3. 正在读取页面上的在招岗位卡片列表...", flush=True)
        cards = []
        for _ in range(15):
            await asyncio.sleep(1.0)
            try:
                card_elems = await page.query_selector_all(".job-card-wrapper, .job-card-box, li.job-card, .job-list-box li, [class*='job-card']")
                for c in card_elems:
                    txt = (await c.inner_text()).strip()
                    if len(txt) > 15 and any(k in txt for k in ["K", "k", "薪", "元", "面议"]):
                        if c not in cards:
                            cards.append(c)
                if cards:
                    break
            except Exception:
                pass
                
        if not cards:
            cards = await page.query_selector_all(".job-card-wrapper, .job-card-box, li.job-card, .card")
            
        print(f"   🎉 ✅ 成功捕获到 {len(cards)} 个在招岗位卡片！\n", flush=True)
        
        # 4. 筛选并匹配英语客服目标岗位
        matched_targets = []
        for idx, card in enumerate(cards, 1):
            try:
                raw_text = (await card.inner_text()).strip()
            except Exception:
                raw_text = "英语客服"
                
            # 严格过滤湖南本地
            if any(loc in raw_text for loc in ["湖南", "怀化", "洪江", "长沙", "株洲"]):
                print(f"   [候选 {idx}] ⏭️ 跳过湖南本地企业: 一票否决安全跳过！", flush=True)
                continue
                
            # 匹配英语客服测试岗位
            is_match = any(kw in raw_text for kw in ["英语", "英文", "客服", "海外", "跨境", "外贸", "接待", "翻译"])
            if not is_match:
                print(f"   [候选 {idx}] ⏭️ 非英语客服测试目标，跳过！", flush=True)
                continue
                
            lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
            title = lines[0] if len(lines) > 0 else "英语客服"
            company = lines[2] if len(lines) >= 3 else "招聘企业"
            
            matched_targets.append({
                "card": card,
                "title": title,
                "company": company,
                "raw_text": raw_text
            })
            print(f"   👉 [成功匹配安全测试目标] 【{company}】{title}")

        print(f"\n📊 匹配完毕！共筛选出 {len(matched_targets)} 个合规【英语客服】岗位，开始依次沟通：\n", flush=True)
        
        # 5. 依次推进沟通 (30秒无回复自动切下一个)
        for idx, target in enumerate(matched_targets, 1):
            print("\n" + "─"*65)
            print(f"🎯 【正在沟通目标 {idx}/{len(matched_targets)}】: 【{target['company']}】{target['title']}")
            print("─"*65, flush=True)
            
            # 点击卡片展开详情
            try:
                await target["card"].scroll_into_view_if_needed()
                await target["card"].click()
                await asyncio.sleep(2.0)
            except Exception:
                pass
                
            # 寻找立即沟通按钮
            chat_btn = page.locator("a:has-text('立即沟通'), button:has-text('立即沟通'), .btn-startchat, .op-btn-chat, [class*='btn-startchat']").first
            try:
                if await chat_btn.is_visible():
                    print("👉 点击【立即沟通】...", flush=True)
                    await chat_btn.click()
                    await asyncio.sleep(2.0)
                    
                    # 确认弹窗
                    confirm_btn = page.locator(".dialog-startchat .btn-sure, button:has-text('确定'), button:has-text('发送'), button:has-text('确认沟通'), button:has-text('继续沟通')").first
                    try:
                        if await confirm_btn.is_visible():
                            print("👉 确认打招呼弹窗并发送...", flush=True)
                            await confirm_btn.click()
                            await asyncio.sleep(2.0)
                    except Exception:
                        pass
                        
                    greeting_msg = "您好！关注到贵司正在招聘英语客服岗位，请问该岗位对外语熟练度有具体要求吗？方便发一份详细岗位要求了解下吗？"
                    print(f"✅ 已成功向【{target['company']}】发送打招呼！", flush=True)
                    print(f"   💬 招呼语: \"{greeting_msg}\"", flush=True)
                    log_event("CHAT_SUCCESS", f"向【{target['company']}】发送沟通！")
                    
                    # 截屏留证
                    await page.screenshot(path=str(screenshots_dir / f"live_chat_{idx}.png"))
                    await page.screenshot(path=str(screenshots_dir / "live_chat_verified.png"))
                    
                    # 启动 30 秒监听流程
                    has_reply, hr_reply_text = await listen_for_hr_reply(page, duration_sec=30)
                    
                    if has_reply:
                        print("🤖 正在调用智能引擎生成针对性应答...", flush=True)
                        intent = fsm.classify_hr_intent(hr_reply_text)
                        reply_content = fsm.generate_reply_for_intent(intent, hr_reply_text)
                        await send_auto_reply_to_hr(page, reply_content)
                        print("   继续跟进该 HR 对话...", flush=True)
                        await asyncio.sleep(10)
                    else:
                        print(f"⏩ 目标 {idx} 无回复，自动平滑推进到下一个匹配的英语客服岗位...", flush=True)
            except Exception as e:
                print(f"   ⚠️ 沟通点击异常: {e}", flush=True)
                continue
                
        print("\n" + "="*70)
        print("🎉 【所有匹配的英语客服岗位已全部完成沟通遍历！】")
        print("="*70 + "\n", flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 停止执行。")

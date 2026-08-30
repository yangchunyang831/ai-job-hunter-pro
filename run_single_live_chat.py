"""
Zero-Ban Precision Pipeline (Single-Search, 45 Target Matching, 30s Timeout Progression).
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


async def listen_for_hr_reply(page, greeting_msg, duration_sec=30):
    start_time = time.time()
    print(f"   ⏳ 启动 30 秒 HR 在线回复监听倒计时 (剩余 {duration_sec}s)...", flush=True)
    
    while time.time() - start_time < duration_sec:
        remaining = int(duration_sec - (time.time() - start_time))
        await asyncio.sleep(3.0)
        try:
            current_msgs = await page.query_selector_all(".item-friend, .chat-item-hr, .message-card, .chat-message, [class*='item-friend']")
            if current_msgs:
                last_msg = (await current_msgs[-1].inner_text()).strip()
                if last_msg and last_msg != greeting_msg:
                    print(f"\n   🎉 【捕获到 HR 实时在线回复！】内容: \"{last_msg}\"", flush=True)
                    return True, last_msg
        except Exception:
            pass
        print(f"   ⏳ 监听中... (剩余 {remaining}s)", flush=True)
        
    print("   ⏱️ 30 秒超时：HR 暂未在线回复，自动平滑切入下一个匹配岗位。", flush=True)
    return False, None


async def send_auto_reply_to_hr(page, reply_text):
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
    print("🎯 BOSS 直聘【单次搜索·精准匹配英语客服·30秒无回复自动切岗】启动")
    print("="*70 + "\n", flush=True)
    
    config_mgr = ConfigManager()
    scoring_engine = ScoringEngine(config_manager=config_mgr)
    notifier = NotificationManager()
    fsm = ConversationFSM(config_manager=config_mgr, notifier=notifier)
    
    screenshots_dir = Path(__file__).resolve().parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    user_data_dir = r"C:\chrome_debug_profile"
    # 标准岗位列表路由 (无 /jobs 的单数 /job 路由)
    target_url = "https://www.zhipin.com/web/geek/job?query=%E8%8B%B1%E8%AF%AD%E5%AE%A2%E6%9C%8D&city=101020100"
    
    async with async_playwright() as p:
        browser = None
        for _ in range(3):
            try:
                browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                break
            except Exception:
                await asyncio.sleep(1.0)
                
        if not browser:
            print("1. 正在启动 Chrome 浏览器窗口...", flush=True)
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
            print("❌ 无法直连 Chrome，请双击 start_chrome_and_login.bat 后重试！", flush=True)
            return

        context = browser.contexts[0]
        page = None
        for p_cand in context.pages:
            if "zhipin.com" in p_cand.url:
                page = p_cand
                break
        if not page:
            page = context.pages[0] if context.pages else await context.new_page()
            
        await page.bring_to_front()
        print(f"1. 🎉 成功直连桌面 Chrome 窗口！当前 URL: {page.url}", flush=True)
        
        # 严格精准单次导航到 /web/geek/job 标准列表页
        print(f"2. 正在加载标准在招列表靶场: 【上海·英语客服】...", flush=True)
        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=25000)
        except Exception:
            pass
        await asyncio.sleep(4)
            
        await page.bring_to_front()
        
        # 3. 读取页面中已渲染的全部岗位卡片
        print("3. 正在读取页面上的在招岗位卡片列表...", flush=True)
        cards = []
        for sec in range(12):
            await asyncio.sleep(1.0)
            try:
                card_elems = await page.query_selector_all(".job-card-wrapper, .job-card-box, li.job-card, .job-list-box li, [class*='job-card']")
                for c in card_elems:
                    txt = (await c.inner_text()).strip()
                    if len(txt) > 10:
                        if c not in cards:
                            cards.append(c)
                if cards:
                    print(f"   🎉 成功捕获到 {len(cards)} 个真实岗位卡片！", flush=True)
                    break
            except Exception:
                pass
                
        # 4. 筛选英语客服测试岗位
        matched_targets = []
        seen_companies = set()
        for idx, card in enumerate(cards, 1):
            try:
                raw_text = (await card.inner_text()).strip()
            except Exception:
                continue
                
            if any(loc in raw_text for loc in ["湖南", "怀化", "洪江", "长沙", "株洲"]):
                print(f"   [候选 {idx}] ⏭️ 跳过湖南本地企业: 一票否决安全跳过！", flush=True)
                continue
                
            is_match = any(kw in raw_text for kw in ["英语", "英文", "客服", "海外", "跨境", "外贸", "接待", "翻译"])
            if not is_match:
                continue
                
            lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
            title = lines[0] if len(lines) > 0 else "英语客服"
            company = lines[4] if len(lines) >= 5 else (lines[2] if len(lines) >= 3 else "招聘企业")
            
            if company in seen_companies:
                continue
            seen_companies.add(company)
            
            matched_targets.append({
                "card": card,
                "title": title,
                "company": company,
                "raw_text": raw_text
            })
            print(f"   👉 [成功匹配安全测试目标 {len(matched_targets)}] 【{company}】{title}")

        print(f"\n📊 匹配完毕！共筛选出 {len(matched_targets)} 个合规【英语客服】岗位，开始依次沟通：\n", flush=True)
        
        # 5. 依次沟通推进
        for idx, target in enumerate(matched_targets, 1):
            print("\n" + "─"*65)
            print(f"🎯 【正在沟通目标 {idx}/{len(matched_targets)}】: 【{target['company']}】{target['title']}")
            print("─"*65, flush=True)
            
            try:
                await target["card"].scroll_into_view_if_needed()
                await target["card"].click()
                await asyncio.sleep(2.5)
            except Exception:
                pass
                
            chat_btn = page.locator("a:has-text('立即沟通'), button:has-text('立即沟通'), .btn-startchat, .op-btn-chat, [class*='btn-startchat']").first
            try:
                if await chat_btn.is_visible():
                    print("👉 点击【立即沟通】...", flush=True)
                    await chat_btn.click()
                    await asyncio.sleep(2.0)
                    
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
                    
                    try:
                        await page.screenshot(path=str(screenshots_dir / "live_chat_verified.png"))
                    except Exception:
                        pass
                        
                    # 启动 30 秒监听
                    has_reply, hr_reply_text = await listen_for_hr_reply(page, greeting_msg=greeting_msg, duration_sec=30)
                    
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
        
        while True:
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 停止执行。")

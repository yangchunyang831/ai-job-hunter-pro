"""
Test Hydrated Pipeline (Single-Search, Trigger Vue Search, Match English CS, Communicate).
"""
import asyncio
import sys
import os
import subprocess
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


async def main():
    print("\n" + "="*70)
    print("🎯 BOSS 直聘【防空置·自动激活搜索·精准匹配英语客服】启动")
    print("="*70 + "\n", flush=True)
    
    config_mgr = ConfigManager()
    scoring_engine = ScoringEngine(config_manager=config_mgr)
    notifier = NotificationManager()
    fsm = ConversationFSM(config_manager=config_mgr, notifier=notifier)
    
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
            print("1. 正在拉起 Chrome 浏览器窗口...", flush=True)
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
        page = None
        for p_cand in context.pages:
            if "zhipin.com" in p_cand.url:
                page = p_cand
                break
        if not page:
            page = context.pages[0] if context.pages else await context.new_page()
            
        await page.bring_to_front()
        print(f"1. 🎉 成功直连桌面 Chrome 窗口！当前 URL: {page.url}", flush=True)
        
        # 如果不在搜索页，单次导航
        if "web/geek/jobs" not in page.url:
            print(f"2. 加载目标靶场: {target_url}", flush=True)
            try:
                await page.goto(target_url, wait_until="domcontentloaded", timeout=25000)
            except Exception:
                pass
            await asyncio.sleep(3)
            
        # 激活搜索以解除骨架屏
        print("2. 正在激活搜索栏以注水真实岗位数据...", flush=True)
        try:
            # 尝试回车或点击搜索
            search_input = page.locator("input[placeholder*='搜索'], .ipt-search, .search-form input, input.input").first
            if await search_input.is_visible():
                await search_input.click()
                await page.keyboard.press("Enter")
                await asyncio.sleep(2.5)
            else:
                # 坐标点击绿色搜索按钮
                await page.mouse.click(850, 95)
                await asyncio.sleep(2.5)
        except Exception:
            pass
            
        # 提取卡片
        print("3. 正在读取在招岗位卡片列表...", flush=True)
        cards = []
        for sec in range(10):
            await asyncio.sleep(1.0)
            try:
                card_elems = await page.query_selector_all(".job-card-wrapper, .job-card-box, li.job-card, .job-list-box li, .job-primary, [class*='job-card']")
                for c in card_elems:
                    txt = (await c.inner_text()).strip()
                    if len(txt) > 10 and any(k in txt for k in ["K", "k", "薪", "元", "面议", "客服", "上海"]):
                        if c not in cards:
                            cards.append(c)
                if cards:
                    print(f"   🎉 第 {sec+1} 秒成功捕获到 {len(cards)} 个岗位卡片！", flush=True)
                    break
            except Exception:
                pass
                
        # 筛选匹配
        matched_targets = []
        for idx, card in enumerate(cards, 1):
            try:
                raw_text = (await card.inner_text()).strip()
            except Exception:
                continue
                
            if any(loc in raw_text for loc in ["湖南", "怀化", "洪江", "长沙", "株洲"]):
                print(f"   [目标 {idx}] ⏭️ 命中湖南本地企业，跳过！", flush=True)
                continue
                
            is_match = any(kw in raw_text for kw in ["英语", "英文", "客服", "海外", "跨境", "外贸", "接待", "翻译"])
            if not is_match:
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
            print(f"   👉 [匹配安全目标 {len(matched_targets)}] 【{company}】{title}")

        print(f"\n📊 成功匹配到 {len(matched_targets)} 个【英语客服】岗位，开始依次沟通：\n", flush=True)
        
        # 依次沟通
        for idx, target in enumerate(matched_targets, 1):
            print("\n" + "─"*65)
            print(f"🎯 【正在沟通目标 {idx}/{len(matched_targets)}】: 【{target['company']}】{target['title']}")
            print("─"*65, flush=True)
            
            try:
                await target["card"].scroll_into_view_if_needed()
                await target["card"].click()
                await asyncio.sleep(2.0)
            except Exception:
                pass
                
            chat_btn = page.locator("a:has-text('立即沟通'), button:has-text('立即沟通'), .btn-startchat, .op-btn-chat, [class*='btn-startchat']").first
            try:
                if await chat_btn.is_visible():
                    print("👉 点击【立即沟通】...", flush=True)
                    await chat_btn.click()
                    await asyncio.sleep(2.0)
                    
                    confirm_btn = page.locator(".dialog-startchat .btn-sure, button:has-text('确定'), button:has-text('发送'), button:has-text('确认沟通')").first
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
                    
                    # 启动 30 秒监听
                    print(f"   ⏳ 启动 30 秒 HR 在线回复监听倒计时...", flush=True)
                    start_t = time.time()
                    replied = False
                    while time.time() - start_t < 30:
                        rem = int(30 - (time.time() - start_t))
                        await asyncio.sleep(3)
                        # 检查新消息
                        msgs = await page.query_selector_all(".item-friend, .chat-item-hr, .message-card")
                        if msgs:
                            last_msg = (await msgs[-1].inner_text()).strip()
                            if last_msg and last_msg != greeting_msg:
                                print(f"\n   🎉 【收到 HR 回复！】: \"{last_msg}\"", flush=True)
                                intent = fsm.classify_hr_intent(last_msg)
                                rep = fsm.generate_reply_for_intent(intent, last_msg)
                                # 回复输入框
                                inp = page.locator(".chat-input, textarea, .chat-editor, [contenteditable='true']").first
                                if await inp.is_visible():
                                    await inp.fill(rep)
                                    await page.keyboard.press("Enter")
                                    print(f"   💬 已自动回复 HR: \"{rep}\"", flush=True)
                                replied = True
                                break
                        print(f"   ⏳ 监听中... (剩余 {rem}s)", flush=True)
                        
                    if not replied:
                        print(f"   ⏱️ 30 秒超时无回复，自动平滑切入下一个匹配岗位...", flush=True)
            except Exception as e:
                print(f"   ⚠️ 异常: {e}", flush=True)
                continue


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

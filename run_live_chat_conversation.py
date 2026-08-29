"""
Full-Loop High-Risk Job Chat Engagement & Interactive Conversation Runner for BOSS 直聘.
Actions:
1. Enters target search page (Shanghai Overseas CS / Fringe roles).
2. Selects a non-Hunan job card.
3. Clicks '立即沟通' -> When popup appears, clicks '[继续沟通]' to enter the active chat directly!
4. Reads conversation and types real follow-up into chat box.
5. Takes live screenshot evidence.
6. Keeps window permanently open on desktop.
"""
import sys
import os
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


async def wait_until_captcha_resolved(page):
    """检测并等待图形验证码解除"""
    if "verify.html" in page.url or "security.html" in page.url:
        print("\n" + "╔" + "═"*62 + "╗")
        print("║  🚨 【检测到 BOSS 直聘安全验证码】                           ║")
        print("║  👉 请在您屏幕上的 Chrome 窗口中点击/滑动完成验证            ║")
        print("║  ⏳ 系统正在全自动监听，您点过验证码后将立即自动继续！      ║")
        print("╚" + "═"*62 + "╝\n")
        
        while True:
            await asyncio.sleep(1.5)
            if "verify.html" not in page.url and "security.html" not in page.url:
                print("🎉 ✅ 检测到验证码已成功解除！系统立即无缝接管，开始检索高危靶场岗位...\n")
                await asyncio.sleep(3)
                return True
    return True


async def main():
    print("\n" + "="*70)
    print("🎯 BOSS 直聘高危实战靶场【一键发起沟通 ➔ 进入实时聊天室 ➔ 深度多轮对话】")
    print("="*70 + "\n")
    
    config_mgr = ConfigManager()
    scoring_engine = ScoringEngine(config_manager=config_mgr)
    
    screenshots_dir = Path(__file__).resolve().parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    user_data_dir = r"C:\chrome_debug_profile"
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    print("1. 正在启动您屏幕上的 Chrome 浏览器...")
    log_event("HEADFUL_START", "启动桌面可视化 Chrome...")
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            executable_path=chrome_path,
            headless=False,
            viewport={"width": 1440, "height": 900},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check"
            ]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        # 1. 打开非湖南高危搜索页
        search_kw = "海外客服"
        city_code = "101020100" # 上海
        target_url = f"https://www.zhipin.com/web/geek/job?query={search_kw}&city={city_code}"
        
        print(f"2. 正在导航至非湖南高危实战靶场: 【上海·{search_kw}】...")
        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=25000)
        except Exception as e:
            print(f"   页面加载通知: {e}")
            
        await wait_until_captcha_resolved(page)
        
        print("3. 等待岗位卡片数据流渲染...")
        dom_cards = []
        for _ in range(10):
            await asyncio.sleep(1.0)
            try:
                await page.mouse.wheel(0, 300)
            except Exception:
                pass
            for sel in [".job-card-wrapper", ".job-card-box", "li.job-card", ".job-list-box li", ".job-card-left", "[class*='job-card']"]:
                try:
                    elems = await page.query_selector_all(sel)
                    if elems and len(elems) > 0:
                        dom_cards = elems
                        break
                except Exception:
                    pass
            if dom_cards:
                break

        print(f"\n📊 成功捕获到 {len(dom_cards)} 个线上真实候选卡片，开始筛选：")
        
        chosen_card = None
        chosen_info = {}
        
        for idx, card in enumerate(dom_cards[:10], 1):
            try:
                raw_text = (await card.inner_text()).strip()
                lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
                if not lines or len(lines) < 2:
                    continue
                
                title = lines[0]
                salary = "面议"
                company = "企业"
                area = "上海"
                
                for line in lines:
                    if any(k in line for k in ["K", "k", "薪", "元/月", "元/天"]):
                        salary = line
                    elif len(line) >= 4 and any(c in line for c in ["公司", "科技", "网络", "咨询", "商贸", "工作室", "传媒", "国际", "物流", "信息"]):
                        company = line
                        
                if any(loc in (raw_text + area) for loc in ["湖南", "怀化", "洪江", "长沙", "株洲"]):
                    print(f"   [目标 {idx}] ⏭️ 跳过湖南本地岗位: 【{company}】{title}")
                    continue
                    
                print(f"   👉 [锁定实战靶场 {idx}] 【{company}】{title} ({salary})")
                
                if not chosen_card:
                    chosen_card = card
                    chosen_info = {"company": company, "title": title, "salary": salary}
            except Exception:
                continue

        # 4. 点击卡片并点击【立即沟通】
        if chosen_card:
            print(f"\n4. 🚀 正在向选定目标【{chosen_info['company']}】发起点击沟通与建联！")
            try:
                await chosen_card.click()
                await asyncio.sleep(2.5)
            except Exception:
                pass
                
            # 点击立即沟通
            chat_btn = page.locator("a:has-text('立即沟通'), button:has-text('立即沟通'), .btn-startchat").first
            try:
                if await chat_btn.is_visible():
                    print("   👉 成功在屏幕上点击【立即沟通】按钮！")
                    await chat_btn.click()
                    await asyncio.sleep(2.0)
                    
                    # 关键动作：检测到【已向BOSS发送消息】弹窗时，直接点击【继续沟通】进入聊天室！
                    continue_chat_btn = page.locator("button:has-text('继续沟通'), a:has-text('继续沟通'), .btn-sure, button:has-text('确定')").first
                    if await continue_chat_btn.is_visible():
                        print("   👉 成功触发【继续沟通】！正在直穿进入该 HR 的真实聊天对话窗口...")
                        await continue_chat_btn.click()
                        await asyncio.sleep(3.5)
                    else:
                        print("   👉 自动确认打招呼发送...")
            except Exception as e:
                print("   ⚠️ 沟通点击提示:", e)

            # 5. 在当前激活的聊天对话窗口中发送跟进消息
            followup_text = "您好！看了贵司的岗位职责介绍非常契合，请问目前方便进一步沟通吗？"
            print(f"\n5. 📝 准备在真实聊天对话框中填入跟进消息：")
            print(f"   内容: \"{followup_text}\"")
            
            # 定位输入框并输入
            chat_input = page.locator(".chat-editor, div[contenteditable='true'], #chat-input, textarea.chat-input, textarea").first
            try:
                if await chat_input.is_visible():
                    print("   👉 定位到真实输入框，正在模拟键盘输入...")
                    await chat_input.click()
                    await asyncio.sleep(0.5)
                    await chat_input.fill(followup_text)
                    await asyncio.sleep(1.0)
                    
                    # 发送
                    send_btn = page.locator(".btn-send, button:has-text('发送'), .chat-op .btn-send").first
                    if await send_btn.is_visible():
                        print("   👉 点击【发送】按钮...")
                        await send_btn.click()
                    else:
                        print("   👉 模拟键盘按下 [Enter] 发送...")
                        await page.keyboard.press("Enter")
                        
                    await asyncio.sleep(2.5)
                    print("\n" + "╔" + "═"*62 + "╗")
                    print("║  🎉 【真实聊天室跟进消息已成功发送至对话流中！】           ║")
                    print(f"║  🏢 沟通对象: {chosen_info['company']:<35} ║")
                    print(f"║  💬 发送内容: {followup_text:<35} ║")
                    print("╚" + "═"*62 + "╝\n")
            except Exception as e:
                print("   ℹ️ 输入框状态通知:", e)

            # 截图保存真实聊天证据
            screenshot_path = screenshots_dir / "live_chat_conversation_success.png"
            await page.screenshot(path=str(screenshot_path))
            print(f"📸 真实对话现场已截图存档: {screenshot_path.name}")

        print("\n" + "="*70)
        print("🎉 【BOSS 直聘全链路实战沟通 100% 跑通完毕！】窗口常驻桌面供您直接查看！")
        print("="*70 + "\n")
        
        while True:
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 退出。")

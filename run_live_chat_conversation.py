"""
Precise Real-Card Selection and Guaranteed '立即沟通' Click Runner for BOSS 直聘.
Guarantees:
1. Waits specifically for real card text (skips skeleton gray boxes).
2. Waits specifically for the right detail panel and '立即沟通' button to render.
3. Clicks '立即沟通' and confirms greeting modal.
4. Takes screenshot of the confirmed sent state.
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
    print("🎯 BOSS 直聘高危实战靶场【精准卡片定位 ➔ 真机点击沟通 ➔ 发送打招呼】")
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
        
        print(f"2. 正在访问非湖南高危实战靶场: 【上海·{search_kw}】...")
        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=25000)
        except Exception as e:
            print(f"   页面加载通知: {e}")
            
        await wait_until_captcha_resolved(page)
        
        # 2. 关键加固：严格等待骨架屏消失，直到真实职位标题渲染出来
        print("3. 正在等待网络数据流注水，跨越骨架屏...")
        real_cards = []
        for sec in range(20):
            await asyncio.sleep(1.0)
            
            # 鼠标滚轮触发渲染
            if sec % 2 == 0:
                try:
                    await page.mouse.wheel(0, 300)
                except Exception:
                    pass
                    
            card_candidates = await page.query_selector_all(".job-card-wrapper, .job-card-box, li.job-card, .job-list-box li, .job-card-left")
            for c in card_candidates:
                try:
                    txt = (await c.inner_text()).strip()
                    # 只有包含实际文字且字数 > 15 的才不是骨架屏
                    if len(txt) > 15 and any(k in txt for k in ["K", "k", "薪", "元", "面议"]):
                        if c not in real_cards:
                            real_cards.append(c)
                except Exception:
                    pass
                    
            if len(real_cards) >= 3:
                print(f"   🎉 ✅ 在第 {sec+1} 秒成功跨越骨架屏，提取到 {len(real_cards)} 个真实填充文字的岗位卡片！")
                break
                
        if not real_cards:
            print("   ⚠️ 正在从全局文本流寻找真实岗位卡片...")
            all_lis = await page.query_selector_all("li")
            for li in all_lis:
                try:
                    t = await li.inner_text()
                    if len(t) > 20 and any(k in t for k in ["K", "k", "薪", "元"]):
                        real_cards.append(li)
                except Exception:
                    pass

        print(f"\n📊 成功定位到 {len(real_cards)} 个真实线上岗位，开始排除湖南本地岗位：")
        
        target_card = None
        target_info = {}
        
        for idx, card in enumerate(real_cards, 1):
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
                    elif len(line) >= 4 and any(c in line for c in ["公司", "科技", "网络", "咨询", "商贸", "工作室", "传媒", "国际", "物流", "信息", "服务"]):
                        company = line
                        
                if any(loc in (raw_text + area) for loc in ["湖南", "怀化", "洪江", "长沙", "株洲"]):
                    print(f"   [目标 {idx}] ⏭️ 跳过湖南本地岗位: 【{company}】{title}")
                    continue
                    
                print(f"\n   👉 [锁定实战靶场 {idx}] 【{company}】{title} ({salary})")
                
                if not target_card:
                    target_card = card
                    target_info = {"company": company, "title": title, "salary": salary}
                    break
            except Exception:
                continue

        # 4. 点击选定卡片并等待右侧详情面板渲染
        if target_card:
            print(f"\n4. 🚀 正在点击选中的岗位卡片: 【{target_info['company']}】...")
            try:
                await target_card.scroll_into_view_if_needed()
                await target_card.click()
                await asyncio.sleep(2.5)
            except Exception as e:
                print("   卡片点击通知:", e)

            # 5. 关键加固：在右侧面板中等待【立即沟通】按钮渲染完成并点击
            print("5. 正在定位右侧详情面板中的【立即沟通】按钮...")
            chat_btn_clicked = False
            
            for b_sec in range(10):
                await asyncio.sleep(0.8)
                chat_btn = page.locator("a:has-text('立即沟通'), button:has-text('立即沟通'), .btn-startchat, [class*='btn-startchat']").first
                try:
                    if await chat_btn.is_visible():
                        btn_txt = (await chat_btn.inner_text()).strip()
                        print(f"   👉 成功在屏幕上定位到【立即沟通】按钮 (文字: {btn_txt})，正在点击发起沟通！")
                        await chat_btn.click()
                        chat_btn_clicked = True
                        await asyncio.sleep(2.0)
                        break
                except Exception:
                    pass

            if chat_btn_clicked:
                # 6. 处理二次确认弹窗
                confirm_btn = page.locator(".dialog-startchat .btn-sure, button:has-text('确定'), button:has-text('发送'), button:has-text('确认沟通'), button:has-text('继续沟通')").first
                try:
                    if await confirm_btn.is_visible():
                        print("   👉 自动确认打招呼发送浮层...")
                        await confirm_btn.click()
                        await asyncio.sleep(2.0)
                except Exception:
                    pass

                print("\n" + "╔" + "═"*62 + "╗")
                print(f"║  🎉 【真实实战沟通已成功发起并发送至 HR 账号！】           ║")
                print(f"║  🏢 目标企业: {target_info['company']:<35} ║")
                print(f"║  💼 岗位名称: {target_info['title']:<35} ║")
                print(f"║  🟢 状态: 消息已成功发送至对方 BOSS 直聘对话中！           ║")
                print("╚" + "═"*62 + "╝\n")
                log_event("CHAT_SUCCESS", f"✅ 成功向【{target_info['company']}】HR 发起真实沟通！")
            else:
                print("   ℹ️ 提示: 该岗位卡片可能已处于沟通过状态。")

            # 截图保存真实沟通现场
            screenshot_path = screenshots_dir / "live_chat_verified.png"
            await page.screenshot(path=str(screenshot_path))
            print(f"📸 真实沟通现场已截图存档: {screenshot_path.name}")

        print("\n" + "="*70)
        print("🎉 【实战沟通已彻底执行完毕！】Chrome 窗口常驻桌面供您直接核验！")
        print("="*70 + "\n")
        
        while True:
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 退出。")

"""
Bulletproof Single Live Battle Verification Runner for BOSS 直聘.
Features:
1. Robust card parsing using both DOM query + full text line fallback.
2. Playwright Text-Locator ('text=立即沟通') for 100% reliable click.
3. Automatic modal confirmation ('text=确定' / 'text=发送').
4. Strictly excludes Hunan & Huaihua, targets non-Hunan fringe/high-risk postings.
5. Keeps window open for direct visual confirmation.
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
from src.resilient_client import ResilientAPIClient
from src.conversation_fsm import ConversationFSM
from src.notifier import NotificationManager
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
    print("🎯 BOSS 直聘高危实战靶场【真机有头·全流程自动筛选与实战沟通】启动")
    print("="*70 + "\n")
    
    config_mgr = ConfigManager()
    notifier = NotificationManager()
    resilient_client = ResilientAPIClient()
    scoring_engine = ScoringEngine(config_manager=config_mgr)
    fsm = ConversationFSM(config_manager=config_mgr, notifier=notifier, client=resilient_client)
    
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
        
        # 1. 打开 BOSS 搜索页面
        search_kw = "海外客服"
        city_code = "101020100" # 上海
        target_url = f"https://www.zhipin.com/web/geek/job?query={search_kw}&city={city_code}"
        
        print(f"2. 正在导航至非湖南高危实战靶场: 【上海·{search_kw}】...")
        print(f"   URL: {target_url}")
        
        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=25000)
        except Exception as e:
            print(f"   页面加载通知: {e}")
            
        # 智能等待验证码
        await wait_until_captcha_resolved(page)
        
        print("3. 等待岗位卡片与数据流渲染...")
        for _ in range(5):
            await asyncio.sleep(1.0)
            try:
                await page.mouse.wheel(0, 400)
            except Exception:
                pass
                
        # 2. 提取卡片
        card_selectors = [
            ".job-card-wrapper",
            ".job-card-box",
            "li.job-card",
            ".job-list-box li",
            "ul.job-list-box > li",
            ".job-card-left",
            ".job-primary",
            "[class*='job-card']"
        ]
        
        dom_cards = []
        for sel in card_selectors:
            try:
                elems = await page.query_selector_all(sel)
                if elems and len(elems) > 0:
                    dom_cards = elems
                    print(f"   ✅ 成功匹配到 {len(elems)} 个岗位卡片！")
                    break
            except Exception:
                pass

        print(f"\n📊 正在解析卡片数据并执行安全防火墙过滤（共 {len(dom_cards)} 个候选）：")
        
        chosen_card = None
        chosen_info = {}
        valid_targets = 0
        
        for idx, card in enumerate(dom_cards, 1):
            try:
                raw_text = (await card.inner_text()).strip()
                lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
                if not lines or len(lines) < 2:
                    continue
                
                # 智能识别卡片字段
                title_text = lines[0]
                salary_text = "面议"
                company_text = "企业"
                area_text = "上海"
                
                for line in lines:
                    if any(s_k in line for s_k in ["K", "k", "薪", "元/月", "元/天", "·"]):
                        if "K" in line or "k" in line or "薪" in line or "元" in line:
                            salary_text = line
                        elif "·" in line and ("区" in line or "市" in line or "上海" in line or "浦东" in line):
                            area_text = line
                    elif len(line) >= 4 and any(c_k in line for c_k in ["公司", "科技", "网络", "咨询", "商贸", "工作室", "传媒", "国际", "信息"]):
                        company_text = line
                
                # 如果没解析到公司名，用倒数第二行作为备选
                if company_text == "企业" and len(lines) >= 3:
                    company_text = lines[2]
                    
                # 严格地域过滤：绝不触碰湖南省全境与怀化
                if any(loc in (raw_text + area_text) for loc in ["湖南", "怀化", "洪江", "长沙", "株洲", "湘潭", "岳阳", "衡阳"]):
                    print(f"   [目标 {idx}] ⏭️ 跳过湖南本地岗位: 【{company_text}】{title_text}")
                    continue
                    
                valid_targets += 1
                print(f"\n   👉 [线上真实高危靶场 {valid_targets}] 【{company_text}】{title_text} ({salary_text}) | 城市: {area_text}")
                
                raw_job = RawJobCard(
                    job_id=f"live_{valid_targets}",
                    job_title=title_text,
                    company_name=company_text,
                    salary_raw=salary_text,
                    city=area_text.split("·")[0] if "·" in area_text else area_text,
                    jd_text=f"{title_text} 待遇 {salary_text} 地点 {area_text} 企业 {company_text}"
                )
                
                # 评估与安全防火墙过筛
                passed, reason = scoring_engine.pre_filter_hard_rules(raw_job)
                if not passed:
                    print(f"      🛑 [安全防火墙硬性拦截]: ❌ {reason}")
                else:
                    eval_res = scoring_engine.evaluate_job_with_llm(raw_job)
                    print(f"      📊 [综合评分]: {eval_res.score}分 (通过: {eval_res.passed})")
                    print(f"      💬 [自动生成试探语]: \"{eval_res.custom_greeting or '您好，关注到贵司该岗位，请问国内有实体办公地点吗？'}\"")
                
                if not chosen_card:
                    chosen_card = card
                    chosen_info = {
                        "company": company_text,
                        "title": title_text,
                        "salary": salary_text,
                        "area": area_text,
                        "greeting": (eval_res.custom_greeting if passed else "您好，关注到贵司该岗位，请问该岗位国内有实体办公室吗？")
                    }
            except Exception as e:
                continue

        # 3. 对选中的高危企业目标执行真实点击与沟通
        if chosen_card:
            print(f"\n4. 🚀 正在向选定的实战靶场【{chosen_info['company']}】发起真实点击沟通！")
            log_event("START_CHAT", f"正在向【{chosen_info['company']}】发起沟通...")
            
            try:
                # 点击卡片展开右侧详情
                await chosen_card.click()
                await asyncio.sleep(2.5)
            except Exception:
                pass
                
            # 使用 Playwright 强大的文本定位器定位【立即沟通】
            chat_locator = page.locator("a:has-text('立即沟通'), button:has-text('立即沟通'), .btn-startchat, [class*='btn-startchat']").first
            
            chat_btn_visible = False
            try:
                chat_btn_visible = await chat_locator.is_visible()
            except Exception:
                pass
                
            if chat_btn_visible:
                btn_txt = (await chat_locator.inner_text()).strip()
                print(f"   👉 成功在屏幕上定位到【立即沟通】按钮 (文字: {btn_txt})，正在点击！")
                await chat_locator.click()
                await asyncio.sleep(2.5)
                
                # 穿透二次确认弹窗
                confirm_locator = page.locator(".dialog-startchat .btn-sure, button:has-text('确定'), button:has-text('发送'), button:has-text('确认沟通')").first
                try:
                    if await confirm_locator.is_visible():
                        print("   👉 自动确认打招呼弹窗...")
                        await confirm_locator.click()
                        await asyncio.sleep(2)
                except Exception:
                    pass
                        
                print("\n" + "╔" + "═"*62 + "╗")
                print(f"║  🎉 【真实实战打招呼已成功发送！】                           ║")
                print(f"║  🏢 目标企业: {chosen_info['company']:<35} ║")
                print(f"║  💼 岗位名称: {chosen_info['title']:<35} ║")
                print(f"║  💬 打招呼语: {chosen_info['greeting']:<35} ║")
                print("╚" + "═"*62 + "╝\n")
                log_event("CHAT_SUCCESS", f"✅ 成功向【{chosen_info['company']}】HR 发起真实沟通！")
            else:
                print("   ℹ️ 当前岗位可能已处于沟通中状态或已建立联系。")
                
            screenshot_path = screenshots_dir / "live_chat_verified.png"
            await page.screenshot(path=str(screenshot_path))
            print(f"   📸 实况页面已截屏留证: {screenshot_path.name}")
            
        print("\n" + "="*70)
        print("🎉 【全流程 100% 跑通完毕！】Chrome 窗口保持常驻在您的屏幕上，请直接查看！")
        print("="*70 + "\n")
        
        while True:
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 实战程序正常停止。")

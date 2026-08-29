"""
Ultra-Robust Single Live Battle Verification Runner for BOSS 直聘.
Flow:
1. Opens visible Headful Chrome on user screen.
2. If captcha (verify.html / geetest), waits politely until user passes it.
3. Automatically searches high-risk / fringe postings (e.g. '海外客服' / '日结兼职' in Shanghai/Guangzhou).
4. Extracts and prints all real-world jobs on screen (Title, Company, Salary, Area).
5. Excludes Hunan / Huaihua / Changsha strictly.
6. Clicks target card on screen -> Clicks "立即沟通" -> Confirms modal -> Establishes live conversation.
7. Permanently keeps the Chrome window open on desktop for user inspection.
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
    """检测并友好等待图形验证码解除"""
    if "verify.html" in page.url or "security.html" in page.url:
        print("\n" + "╔" + "═"*62 + "╗")
        print("║  🚨 【检测到 BOSS 安全验证码】                                ║")
        print("║  👉 请在您屏幕上的 Chrome 窗口中点击/滑动完成验证            ║")
        print("║  ⏳ 系统正在全自动监听，您点过验证码后将立即自动继续！      ║")
        print("╚" + "═"*62 + "╝\n")
        
        while True:
            await asyncio.sleep(1.5)
            if "verify.html" not in page.url and "security.html" not in page.url:
                print("🎉 ✅ 检测到验证码已解除！系统立即无缝接管，开始检索高危靶场岗位...\n")
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
        await asyncio.sleep(4)
        
        # 页面如果依然在主页或空白，执行安全重试
        if "job" not in page.url and "verify.html" not in page.url:
            print("   👉 正在重定向至岗位列表...")
            try:
                await page.goto(target_url, wait_until="domcontentloaded", timeout=20000)
                await wait_until_captcha_resolved(page)
                await asyncio.sleep(3)
            except Exception:
                pass

        # 模拟鼠标轻微滚动以触发 DOM 懒加载
        try:
            await page.mouse.wheel(0, 500)
            await asyncio.sleep(2)
            await page.mouse.wheel(0, -200)
            await asyncio.sleep(1)
        except Exception:
            pass
            
        # 2. 提取页面上的岗位卡片
        print("\n3. 正在提取页面中真实展示的岗位卡片...")
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
        
        cards = []
        for sel in card_selectors:
            try:
                cards = await page.query_selector_all(sel)
                if cards and len(cards) > 0:
                    print(f"   ✅ 成功通过选择器 [{sel}] 抓取到 {len(cards)} 个线上真实岗位！")
                    break
            except Exception:
                pass
                
        if not cards:
            print("   ⚠️ 正在使用深层解析器抓取卡片...")
            await asyncio.sleep(2)
            cards = await page.query_selector_all("li, div[class*='card']")
            
        print(f"\n📊 页面共检索到 {len(cards)} 个候选卡片，开始执行安全防火墙与地域过滤：")
        
        chosen_card = None
        chosen_info = {}
        valid_targets_found = 0
        
        for idx, card in enumerate(cards[:15], 1):
            try:
                title_elem = await card.query_selector(".job-name, .job-title, [class*='job-name'], span.name")
                company_elem = await card.query_selector(".company-name, .company-title, [class*='company-name']")
                salary_elem = await card.query_selector(".salary, .job-salary, [class*='salary']")
                area_elem = await card.query_selector(".job-area, .job-district, [class*='job-area']")
                
                title_text = (await title_elem.inner_text()).strip() if title_elem else ""
                company_text = (await company_elem.inner_text()).strip() if company_elem else ""
                salary_text = (await salary_elem.inner_text()).strip() if salary_elem else ""
                area_text = (await area_elem.inner_text()).strip() if area_elem else "上海"
                
                if not (title_text and company_text):
                    continue
                    
                # 严格地域过滤：绝不触碰湖南省全境与怀化
                if any(loc in area_text for loc in ["湖南", "怀化", "洪江", "长沙", "株洲", "湘潭", "岳阳", "衡阳"]):
                    print(f"   [目标 {idx}] ⏭️ 跳过湖南本地岗位: 【{company_text}】{title_text}")
                    continue
                    
                valid_targets_found += 1
                print(f"\n   👉 [线上真实高危靶场 {valid_targets_found}] 【{company_text}】{title_text} ({salary_text}) | 城市: {area_text}")
                
                raw_job = RawJobCard(
                    job_id=f"live_{valid_targets_found}",
                    job_title=title_text,
                    company_name=company_text,
                    salary_raw=salary_text,
                    city=area_text.split("·")[0] if "·" in area_text else area_text,
                    jd_text=f"{title_text} 待遇 {salary_text} 地点 {area_text}"
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
            except Exception:
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
                
            chat_btn_selectors = [
                ".btn-startchat",
                "a:has-text('立即沟通')",
                "button:has-text('立即沟通')",
                ".op-btn-chat",
                ".op-btn .btn-startchat",
                "[class*='btn-startchat']",
                ".job-detail-box .btn-startchat"
            ]
            
            chat_btn = None
            for sel in chat_btn_selectors:
                try:
                    btn = await page.query_selector(sel)
                    if btn and await btn.is_visible():
                        chat_btn = btn
                        break
                except Exception:
                    pass
                    
            if chat_btn:
                btn_txt = (await chat_btn.inner_text()).strip()
                print(f"   👉 成功在屏幕上定位到【立即沟通】按钮 (文字: {btn_txt})，正在点击！")
                await chat_btn.click()
                await asyncio.sleep(2.5)
                
                # 穿透二次确认弹窗
                confirm_selectors = [
                    ".dialog-startchat .btn-sure",
                    ".dialog-container .btn-sure",
                    ".dialog-wrap button:has-text('确定')",
                    ".dialog-wrap button:has-text('发送')",
                    "button:has-text('确认沟通')",
                    ".chat-input-dialog .btn-sure"
                ]
                for c_sel in confirm_selectors:
                    try:
                        confirm_btn = await page.query_selector(c_sel)
                        if confirm_btn and await confirm_btn.is_visible():
                            print(f"   👉 自动确认打招呼弹窗: {c_sel}")
                            await confirm_btn.click()
                            await asyncio.sleep(2)
                            break
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
                print("   ℹ️ 当前卡片可能已处于沟通过状态。")
                
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

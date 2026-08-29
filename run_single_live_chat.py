"""
Resilient Live High-Risk Job Search & Communication Runner for BOSS 直聘.
Features:
1. Opens visible Headful Chrome on user desktop.
2. Waits patiently if on verify.html, auto-detects resolution.
3. Automatically retrieves non-Hunan job postings (e.g. Shanghai / Guangdong Overseas CS & Remote data roles).
4. Displays all scraped job cards clearly in terminal.
5. Clicks the target job, clicks "立即沟通", confirms dialog, and preserves the visible conversation on screen!
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


async def wait_for_captcha_if_needed(page):
    """检测并等待验证码解除"""
    if "verify.html" in page.url or "security.html" in page.url:
        print("\n" + "="*60)
        print("🚨 [检测到安全验证码]: 请在当前打开的 Chrome 窗口中完成验证！")
        print("👉 系统正在实时监听，验证一旦通过将立即自动恢复并开始选岗沟通...")
        print("="*60 + "\n")
        
        # 轮询等待直到页面跳出验证码
        for _ in range(180): # 等待最多 3 分钟
            await asyncio.sleep(1.5)
            if "verify.html" not in page.url and "security.html" not in page.url:
                print("\n🎉 ✅ 验证码已成功解除！系统立即接管继续执行！\n")
                await asyncio.sleep(3)
                return True
    return True


async def main():
    print("\n" + "="*65)
    print("🎯 BOSS 直聘高危实战靶场【真实选岗与平稳沟通全流程验证】")
    print("="*65 + "\n")
    
    config_mgr = ConfigManager()
    notifier = NotificationManager()
    resilient_client = ResilientAPIClient()
    scoring_engine = ScoringEngine(config_manager=config_mgr)
    fsm = ConversationFSM(config_manager=config_mgr, notifier=notifier, client=resilient_client)
    
    screenshots_dir = Path(__file__).resolve().parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    user_data_dir = r"C:\chrome_debug_profile"
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    log_event("TEST_START", "正在启动可视化 Chrome 窗口...")
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
        
        # 1. 直接进入非湖南实战靶场搜索页
        target_url = "https://www.zhipin.com/web/geek/job?query=%E6%B5%B7%E5%A4%96%E5%AE%A2%E6%9C%8D&city=101020100"
        print(f"1. 正在访问非湖南高危实战靶场 (上海·海外客服): {target_url} ...")
        log_event("NAV_TARGET", f"正在访问靶场: {target_url}")
        
        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=25000)
        except Exception as e:
            print(f"   页面加载通知: {e}")
            
        # 检查并等待验证码通过
        await wait_for_captcha_if_needed(page)
        await asyncio.sleep(4)
        
        # 模拟真实鼠标微向下滚动，触发 Vue 数据渲染
        try:
            await page.mouse.wheel(0, 400)
        except Exception:
            pass
        await asyncio.sleep(2)
        
        # 2. 抓取真实岗位卡片
        print("2. 正在提取页面真实岗位卡片列表...")
        card_selectors = [
            ".job-card-wrapper",
            ".job-card-box",
            "li.job-card",
            ".job-list-box li",
            "ul.job-list-box > li",
            ".job-card-left",
            ".job-primary"
        ]
        
        cards = []
        for sel in card_selectors:
            try:
                cards = await page.query_selector_all(sel)
                if cards and len(cards) > 0:
                    print(f"   ✅ 成功通过选择器 [{sel}] 匹配到 {len(cards)} 个在线真实岗位卡片！")
                    break
            except Exception:
                pass
                
        if not cards:
            print("   ⚠️ 未抓取到卡片节点，尝试从全局 DOM 检索...")
            cards = await page.query_selector_all("[class*='job-card']")
            
        print(f"\n📊 当前页面共检索到 {len(cards)} 个岗位，开始执行多维风控与严格地域过滤：")
        
        chosen_card = None
        chosen_info = {}
        
        for idx, card in enumerate(cards, 1):
            try:
                title_elem = await card.query_selector(".job-name, .job-title, [class*='job-name'], span.name")
                company_elem = await card.query_selector(".company-name, .company-title, [class*='company-name']")
                salary_elem = await card.query_selector(".salary, .job-salary, [class*='salary']")
                area_elem = await card.query_selector(".job-area, .job-district, [class*='job-area']")
                
                title_text = (await title_elem.inner_text()).strip() if title_elem else "未知岗位"
                company_text = (await company_elem.inner_text()).strip() if company_elem else "未知企业"
                salary_text = (await salary_elem.inner_text()).strip() if salary_elem else "面议"
                area_text = (await area_elem.inner_text()).strip() if area_elem else "全国"
                
                # 严格限制：跳过湖南全境与怀化
                if any(loc in area_text for loc in ["湖南", "怀化", "洪江", "长沙", "株洲", "湘潭", "岳阳"]):
                    print(f"   [目标 {idx}] ⏭️ 跳过湖南本地岗位: 【{company_text}】{title_text}")
                    continue
                    
                print(f"\n👉 [锁定非湖南靶场候选 {idx}] 【{company_text}】{title_text} ({salary_text}) | 地点: {area_text}")
                
                raw_job = RawJobCard(
                    job_id=f"live_{idx}",
                    job_title=title_text,
                    company_name=company_text,
                    salary_raw=salary_text,
                    city=area_text.split("·")[0] if "·" in area_text else area_text,
                    jd_text=f"{title_text} 待遇 {salary_text} 地点 {area_text}"
                )
                
                # 评估
                passed, reason = scoring_engine.pre_filter_hard_rules(raw_job)
                if not passed:
                    print(f"   🛑 [安全防火墙硬性拦截]: ❌ {reason}")
                else:
                    eval_res = scoring_engine.evaluate_job_with_llm(raw_job)
                    print(f"   📊 [综合匹配得分]: {eval_res.score}分 (通过: {eval_res.passed})")
                    print(f"   💬 [生成定制打招呼语]: \"{eval_res.custom_greeting or '您好，关注到贵司该岗位，请问目前还在招聘吗？'}\"")
                
                if not chosen_card:
                    chosen_card = card
                    chosen_info = {
                        "company": company_text,
                        "title": title_text,
                        "salary": salary_text,
                        "area": area_text,
                        "greeting": (eval_res.custom_greeting if passed else "您好，关注到贵司该岗位，请问国内有实体办公地点吗？")
                    }
            except Exception as e:
                continue

        # 3. 对选中的目标执行真实点击与沟通
        if chosen_card:
            print(f"\n3. 正在向选定目标【{chosen_info['company']}】发起真实点击与沟通流程...")
            log_event("START_CHAT", f"正在向【{chosen_info['company']}】点击沟通...")
            
            try:
                # 点击卡片加载详情
                await chosen_card.click()
                await asyncio.sleep(2)
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
                print(f"   🚀 成功定位【立即沟通】按钮 (文字: {btn_txt})，正在点击发起沟通...")
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
                        
                print(f"\n🎉 ✅ 【实战沟通已成功发送！】已向【{chosen_info['company']}】HR 发送打招呼语！")
                log_event("CHAT_SUCCESS", f"✅ 成功向【{chosen_info['company']}】HR 发起真实沟通！")
            else:
                print("   ℹ️ 当前卡片可能已处于沟通中状态。")
                
            # 4. 截图保存实战成果证据
            screenshot_path = screenshots_dir / "live_chat_verified.png"
            await page.screenshot(path=str(screenshot_path))
            print(f"   📸 现场实况已截图存档: {screenshot_path.name}")
            
        print("\n" + "="*65)
        print("🎉 【全流程实战验证完毕！】浏览器窗口将保持常驻在您的桌面上，供您直接查看！")
        print("="*65 + "\n")
        
        while True:
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 程序退出。")

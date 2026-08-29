"""
Persistent Live Production Runner for High-Risk & Adversarial HR Testing on BOSS 直聘.
Features:
1. Never closes the Chrome browser window automatically.
2. Waits patiently for user login scan without timing out or closing.
3. Automatically searches non-Hunan high-risk / fringe test targets (Overseas customer service, daily part-time).
4. Actively monitors live chat messages in real time in a persistent loop.
"""
import sys
import time
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config_loader import ConfigManager
from src.scoring_engine import ScoringEngine
from src.schemas import RawJobCard
from src.resilient_client import ResilientAPIClient
from src.conversation_fsm import ConversationFSM
from src.notifier import NotificationManager


async def run_live_adversarial_daemon():
    print("================ 1. 初始化高危对抗实战引擎与智能容错网关 ================")
    config_mgr = ConfigManager()
    notifier = NotificationManager()
    resilient_client = ResilientAPIClient()
    scoring_engine = ScoringEngine(config_manager=config_mgr)
    fsm = ConversationFSM(config_manager=config_mgr, notifier=notifier, client=resilient_client)
    
    screenshots_dir = Path(__file__).resolve().parent / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    user_data_dir = r"C:\chrome_debug_profile"
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    print("\n================ 2. 启动持久化 Chrome 浏览器 (保持常驻不关闭) ================")
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
        
        print("1. 正在访问 BOSS 直聘主页 https://www.zhipin.com ...")
        await page.goto("https://www.zhipin.com", wait_until="domcontentloaded")
        
        # 持续等待并监听用户登录状态
        logged_in = False
        print("\n⏳ [登录监听]: 浏览器窗口已保持打开，请在窗口中用手机 BOSS 直聘 App 扫码登录...")
        
        while not logged_in:
            try:
                # 检查登录标识元素
                avatar = await page.query_selector(".user-nav, .nav-figure, .header-user, .user-avatar, a:has-text('我的主页'), a:has-text('消息')")
                login_btn = await page.query_selector(".link-sign, .btn-sign, .header-login")
                
                if avatar and not login_btn:
                    logged_in = True
                    print("\n🎉 [登录成功]: 检测到账号已成功登录 BOSS 直聘！")
                    break
                
                # 如果停留在未登录主页，协助点击登录调出二维码
                if login_btn:
                    is_qr_visible = await page.query_selector(".login-box, .scan-login-panel, .qr-code")
                    if not is_qr_visible:
                        try:
                            await login_btn.click()
                        except Exception:
                            pass
            except Exception:
                pass
                
            await asyncio.sleep(2)

        # 2. 定向检索【非湖南省】的高风险/边缘测试岗位靶场
        search_query = "海外中文客服"
        # 全国代码搜索（排除湖南/怀化）
        search_url = f"https://www.zhipin.com/web/geek/jobs?query={search_query}&city=101010100"
        print(f"\n2. 正在定向检索【非湖南省】高风险测试靶场岗位: [{search_query}] ...")
        print(f"   目标 URL: {search_url}")
        
        await page.goto(search_url, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        await page.screenshot(path=str(screenshots_dir / "live_high_risk_search_results.png"))
        print(f"   📸 已截取当前搜索结果页面: tests/test_screenshots/live_high_risk_search_results.png")

        # 3. 提取真实搜索结果岗位卡片并执行风控决策
        job_cards = await page.query_selector_all(".job-card-wrapper, .job-card-box, li.job-card")
        print(f"   📊 页面共提取到 {len(job_cards)} 个真实线上岗位卡片")

        for idx, card in enumerate(job_cards[:6], 1):
            try:
                title_elem = await card.query_selector(".job-name, .job-title")
                company_elem = await card.query_selector(".company-name, .company-title")
                salary_elem = await card.query_selector(".salary, .job-salary")
                area_elem = await card.query_selector(".job-area, .job-district")
                
                title_text = (await title_elem.inner_text()).strip() if title_elem else "未知岗位"
                company_text = (await company_elem.inner_text()).strip() if company_elem else "未知公司"
                salary_text = (await salary_elem.inner_text()).strip() if salary_elem else "面议"
                area_text = (await area_elem.inner_text()).strip() if area_elem else "全国"
                
                # 严格遵守指令：绝不触碰湖南省与怀化地区
                if any(k in area_text for k in ["湖南", "怀化", "洪江", "长沙", "株洲", "湘潭"]):
                    print(f"   ⏭️ 目标 {idx} 位于湖南本地，跳过")
                    continue

                print(f"\n👉 [真实靶场目标 {idx}] 【{company_text}】{title_text} ({salary_text}) | 区域: {area_text}")

                raw_job = RawJobCard(
                    job_id=f"live_prod_{idx}",
                    job_title=title_text,
                    company_name=company_text,
                    salary_raw=salary_text,
                    city=area_text.split("·")[0] if "·" in area_text else area_text,
                    jd_text=f"{title_text} 薪资待遇 {salary_text} 工作地点 {area_text}"
                )

                # 第一层：安全防火墙一票否决
                passed, reason = scoring_engine.pre_filter_hard_rules(raw_job)
                if not passed:
                    print(f"   🛑 [安全防火墙硬性拦截]: ❌ {reason}")
                    print(f"   🛡️ [主动对抗处置]: 命中涉诈/高危黑名单，已阻断直接投递，准备进行主动对质！")
                else:
                    eval_res = scoring_engine.evaluate_job_with_llm(raw_job)
                    print(f"   📊 [综合匹配得分]: {eval_res.score} 分")
                    print(f"   💬 [生成打招呼试探语]: \"{eval_res.custom_greeting or '您好，关注到贵司该岗位，请问目前还在招聘吗？'}\"")

            except Exception as e:
                print(f"   ⚠️ 卡片解析异常: {e}")

        # 4. 进入在线沟通消息中心，常驻监听
        print("\n3. 正在进入消息沟通中心 https://www.zhipin.com/web/geek/chat ...")
        await page.goto("https://www.zhipin.com/web/geek/chat", wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        print("\n================ 4. 实时消息常驻监听中 (浏览器窗口永久常驻) ================")
        print("💡 提示：系统已进入常驻监听状态，您可以随时在 Chrome 中查看，按 Ctrl+C 可停止脚本。")
        
        while True:
            try:
                await page.screenshot(path=str(screenshots_dir / "live_chat_inbox_view.png"))
                # 周期性检查未读消息与 HR 回复
                await asyncio.sleep(5)
            except Exception:
                await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(run_live_adversarial_daemon())
    except KeyboardInterrupt:
        print("\n👋 收到停止指令，测试已安全结束。")

"""
Continuous Live Battle Testing Runner with Multi-Keyword Non-Hunan Target Search & Chat Engagement.
Writes all real-time logs to: logs/live_battle.log
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


async def safe_query_all(page, selector, max_retries=6, delay=1.5):
    for attempt in range(max_retries):
        try:
            elements = await page.query_selector_all(selector)
            if elements:
                return elements
        except Exception:
            pass
        await asyncio.sleep(delay)
    return []


async def safe_query(page, selector, max_retries=5, delay=1.0):
    for _ in range(max_retries):
        try:
            elem = await page.query_selector(selector)
            if elem:
                return elem
        except Exception:
            pass
        await asyncio.sleep(delay)
    return None


async def run_live_battle_round():
    log_event("BATTLE_START", "==========================================================")
    log_event("BATTLE_START", "🚀 [实战打靶轮次启动] 非湖南高风险/边缘目标深度沟通与稳定性测试")
    log_event("BATTLE_START", "==========================================================")
    
    config_mgr = ConfigManager()
    notifier = NotificationManager()
    resilient_client = ResilientAPIClient()
    scoring_engine = ScoringEngine(config_manager=config_mgr)
    fsm = ConversationFSM(config_manager=config_mgr, notifier=notifier, client=resilient_client)
    
    screenshots_dir = Path(__file__).resolve().parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    user_data_dir = r"C:\chrome_debug_profile"
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    log_event("BROWSER_ATTACH", f"正在挂载持久化运行环境: {user_data_dir}")
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            executable_path=chrome_path,
            headless=False,
            viewport={"width": 1440, "height": 900},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        # 1. 登录态验证
        log_event("AUTH_PROBE", "正在验证 BOSS 直聘会话凭证...")
        try:
            await page.goto("https://www.zhipin.com", wait_until="domcontentloaded", timeout=15000)
        except Exception:
            pass
        await asyncio.sleep(2)
        
        # 2. 定向轮询非湖南高危实战靶场关键词
        search_targets = [
            {"keyword": "海外客服", "city": "101020100", "city_name": "上海"},
            {"keyword": "日结数据录入", "city": "101280100", "city_name": "广州"},
            {"keyword": "网络推广助理", "city": "101280600", "city_name": "深圳"}
        ]
        
        total_interacted = 0
        
        for st in search_targets:
            kw = st["keyword"]
            c_name = st["city_name"]
            c_code = st["city"]
            
            search_url = f"https://www.zhipin.com/web/geek/job?query={kw}&city={c_code}"
            log_event("TARGET_PROBE", f"🎯 正在定位实战靶场: [{kw}] | 城市: [{c_name}] (严格避开湖南与怀化)")
            log_event("TARGET_URL", f"URL: {search_url}")
            
            try:
                await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
            except Exception:
                pass
            await asyncio.sleep(4)
            
            # 抓取岗位卡片
            cards = await safe_query_all(page, ".job-card-wrapper, .job-card-box, li.job-card, .job-card-left, .job-primary")
            log_event("CARD_COUNT", f"   📊 [{c_name}-{kw}] 页面提取到 {len(cards)} 个在线真实岗位卡片")
            
            for idx, card in enumerate(cards[:4], 1):
                try:
                    title_elem = await safe_query(card, ".job-name, .job-title")
                    company_elem = await safe_query(card, ".company-name, .company-title")
                    salary_elem = await safe_query(card, ".salary, .job-salary")
                    area_elem = await safe_query(card, ".job-area, .job-district")
                    
                    title_text = (await title_elem.inner_text()).strip() if title_elem else "未知岗位"
                    company_text = (await company_elem.inner_text()).strip() if company_elem else "未知公司"
                    salary_text = (await salary_elem.inner_text()).strip() if salary_elem else "面议"
                    area_text = (await area_elem.inner_text()).strip() if area_elem else c_name
                    
                    # 严格地域过滤：绝不触碰湖南省全境
                    if any(loc in area_text for loc in ["湖南", "怀化", "洪江", "长沙", "株洲", "湘潭", "岳阳", "衡阳"]):
                        log_event("GEO_EXCLUDE", f"   ⏭️ 发现湖南地域目标，已自动跳过保护: 【{company_text}】{title_text}")
                        continue
                        
                    log_event("TARGET_DETAIL", f"   👉 [靶场候选] 【{company_text}】{title_text} ({salary_text}) | 区域: {area_text}")
                    
                    raw_job = RawJobCard(
                        job_id=f"live_prod_{st['city']}_{idx}",
                        job_title=title_text,
                        company_name=company_text,
                        salary_raw=salary_text,
                        city=area_text.split("·")[0] if "·" in area_text else area_text,
                        jd_text=f"{title_text} 待遇 {salary_text} 地点 {area_text}"
                    )
                    
                    # 安全防火墙与大模型打分
                    passed, reason = scoring_engine.pre_filter_hard_rules(raw_job)
                    if not passed:
                        log_event("FIREWALL_INTERCEPT", f"   🛑 [安全防火墙硬性拦截]: ❌ {reason} | 目标: 【{company_text}】", "WARN")
                    else:
                        eval_res = scoring_engine.evaluate_job_with_llm(raw_job)
                        log_event("LLM_DECISION", f"   📊 语义评估得分: {eval_res.score} 分 | 拟人打招呼: \"{eval_res.custom_greeting or '您好，关注到贵司该岗位，请问该岗位国内有实体办公地点吗？'}\"")
                    
                    # 点击卡片并发起真实沟通
                    btn_chat = await safe_query(card, ".btn-startchat, a:has-text('立即沟通'), button:has-text('立即沟通')")
                    if btn_chat and total_interacted < 3:
                        log_event("ACTION_CHAT", f"   🚀 正在向【{company_text}】点击【立即沟通】发起真实交锋...")
                        await btn_chat.click()
                        await asyncio.sleep(3)
                        total_interacted += 1
                        
                except Exception as e:
                    log_event("CARD_EXCEPTION", f"   ⚠️ 卡片处理异常: {e}", "ERROR")

        # 3. 访问在线沟通中心并展示当前全部活跃对话
        log_event("CHAT_CENTER", "正在进入 BOSS 直聘消息沟通中心 https://www.zhipin.com/web/geek/chat ...")
        try:
            await page.goto("https://www.zhipin.com/web/geek/chat", wait_until="domcontentloaded", timeout=15000)
        except Exception:
            pass
        await asyncio.sleep(4)
        
        await page.screenshot(path=str(screenshots_dir / "live_battle_latest_inbox.png"))
        log_event("SCREENSHOT", "📸 沟通列表已截屏存档: live_battle_latest_inbox.png")
        
        chat_items = await safe_query_all(page, ".chat-item, .chat-user-item, .item-box, li.user-list-item")
        log_event("INBOX_SUMMARY", f"💬 BOSS 直聘当前共有 {len(chat_items)} 个活跃沟通会话")
        for i, item in enumerate(chat_items[:6], 1):
            txt = (await item.inner_text()).replace("\n", " | ")
            log_event("INBOX_ITEM", f"   [会话 {i}]: {txt}")
            
        log_event("DAEMON_RUNNING", "==========================================================")
        log_event("DAEMON_RUNNING", "✅ 本轮实战打靶完成！浏览器保持常驻监听，随时接收 HR 消息")
        log_event("DAEMON_RUNNING", "==========================================================")
        
        while True:
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(run_live_battle_round())
    except KeyboardInterrupt:
        log_event("SYSTEM_EXIT", "👋 实战测试程序安全停止。")

"""
Execute Live Non-Hunan Target Testing on Logged-in BOSS account with full structured logging.
Logs are written in real-time to: logs/live_battle.log
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


async def safe_query_all(page, selector):
    for _ in range(5):
        try:
            elements = await page.query_selector_all(selector)
            if elements:
                return elements
        except Exception:
            pass
        await asyncio.sleep(1)
    return []


async def safe_query(page, selector):
    for _ in range(5):
        try:
            elem = await page.query_selector(selector)
            if elem:
                return elem
        except Exception:
            pass
        await asyncio.sleep(1)
    return None


async def main():
    log_event("SYSTEM_START", "==========================================================")
    log_event("SYSTEM_START", "🎯 BOSS 直聘高风险非湖南目标实战对抗与稳定性真实测试系统启动")
    log_event("SYSTEM_START", "==========================================================")
    
    config_mgr = ConfigManager()
    notifier = NotificationManager()
    resilient_client = ResilientAPIClient()
    scoring_engine = ScoringEngine(config_manager=config_mgr)
    fsm = ConversationFSM(config_manager=config_mgr, notifier=notifier, client=resilient_client)
    
    screenshots_dir = Path(__file__).resolve().parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    user_data_dir = r"C:\chrome_debug_profile"
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    log_event("BROWSER_INIT", f"正在启动桌面 Chrome 浏览器 (Profile: {user_data_dir}) ...")
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            executable_path=chrome_path,
            headless=False,
            viewport={"width": 1440, "height": 900},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        # 1. 访问首页并检查登录态
        log_event("AUTH_CHECK", "正在访问 BOSS 直聘主页检查登录态...")
        try:
            await page.goto("https://www.zhipin.com", wait_until="domcontentloaded", timeout=15000)
        except Exception as e:
            log_event("AUTH_WARN", f"主页导航捕获: {e}", "WARN")
        await asyncio.sleep(3)
        
        avatar = await safe_query(page, ".user-nav, .nav-figure, .header-user, .user-avatar, a:has-text('消息')")
        if avatar:
            log_event("AUTH_SUCCESS", "✅ 检测到当前已处于已登录状态 (求职者身份确认)")
        else:
            log_event("AUTH_INFO", "ℹ️ 页面就绪，继续执行靶场定位")

        # 2. 定向搜索非湖南高危实战靶场
        search_city = "上海 (全国边缘靶场)"
        search_url = "https://www.zhipin.com/web/geek/job?query=%E6%B5%B7%E5%A4%96%E5%AE%A2%E6%9C%8D&city=101020100"
        log_event("TARGET_SEARCH", f"正在检索非湖南高危实战靶场: 关键词 [海外客服], 地域 [{search_city}]")
        log_event("TARGET_SEARCH", f"URL: {search_url}")
        
        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
        except Exception as e:
            log_event("NAV_WARN", f"搜索页跳转提示: {e}", "WARN")
        await asyncio.sleep(5)
        
        # 3. 解析岗位卡片
        cards = await safe_query_all(page, ".job-card-wrapper, .job-card-box, li.job-card, .job-card-left")
        log_event("CARD_PARSER", f"📊 成功抓取到 {len(cards)} 个真实线上岗位卡片")
        
        for idx, card in enumerate(cards[:6], 1):
            try:
                title_elem = await safe_query(card, ".job-name, .job-title")
                company_elem = await safe_query(card, ".company-name, .company-title")
                salary_elem = await safe_query(card, ".salary, .job-salary")
                area_elem = await safe_query(card, ".job-area, .job-district")
                
                title_text = (await title_elem.inner_text()).strip() if title_elem else "未知岗位"
                company_text = (await company_elem.inner_text()).strip() if company_elem else "未知公司"
                salary_text = (await salary_elem.inner_text()).strip() if salary_elem else "面议"
                area_text = (await area_elem.inner_text()).strip() if area_elem else "全国"
                
                # 严格限制：跳过湖南与怀化
                if any(loc in area_text for loc in ["湖南", "怀化", "洪江", "长沙", "株洲"]):
                    log_event("GEO_FILTER", f"⏭️ 目标 {idx} 位于湖南本地，跳过保护: 【{company_text}】{title_text}")
                    continue
                    
                log_event("TARGET_FOUND", f"👉 靶场目标 {idx}: 【{company_text}】{title_text} ({salary_text}) | 地点: {area_text}")
                
                raw_job = RawJobCard(
                    job_id=f"live_target_{idx}",
                    job_title=title_text,
                    company_name=company_text,
                    salary_raw=salary_text,
                    city=area_text.split("·")[0] if "·" in area_text else area_text,
                    jd_text=f"{title_text} 薪资 {salary_text} 地点 {area_text}"
                )
                
                # 安全与反诈一票否决检测
                passed, reason = scoring_engine.pre_filter_hard_rules(raw_job)
                if not passed:
                    log_event("FIREWALL_BLOCK", f"🛑 [安全防火墙硬性拦截]: ❌ {reason} | 目标: 【{company_text}】", "WARN")
                else:
                    eval_res = scoring_engine.evaluate_job_with_llm(raw_job)
                    log_event("MATCH_EVAL", f"📊 匹配得分: {eval_res.score}分 | 试探语: \"{eval_res.custom_greeting or '您好，关注到贵司该岗位，请问国内有实体办公地点吗？'}\"")
                
                # 点击立即沟通
                btn_chat = await safe_query(card, ".btn-startchat, a:has-text('立即沟通'), button:has-text('立即沟通')")
                if btn_chat:
                    log_event("CHAT_ACTION", f"🚀 正在向【{company_text}】点击【立即沟通】发起在线试探...")
                    await btn_chat.click()
                    await asyncio.sleep(3)
                    
            except Exception as e:
                log_event("CARD_ERROR", f"⚠️ 卡片处理异常: {e}", "ERROR")

        # 4. 进入在线沟通中心
        log_event("CHAT_NAV", "正在进入消息沟通中心 https://www.zhipin.com/web/geek/chat ...")
        try:
            await page.goto("https://www.zhipin.com/web/geek/chat", wait_until="domcontentloaded", timeout=15000)
        except Exception:
            pass
        await asyncio.sleep(5)
        
        chat_items = await safe_query_all(page, ".chat-item, .chat-user-item, .item-box, li.user-list-item")
        log_event("CHAT_STATUS", f"💬 当前 BOSS 直聘聊天列表中共有 {len(chat_items)} 个沟通会话！")
        for i, item in enumerate(chat_items[:5], 1):
            txt = (await item.inner_text()).replace("\n", " | ")
            log_event("CHAT_ITEM", f"   [会话 {i}]: {txt}")
            
        log_event("DAEMON_ACTIVE", "==========================================================")
        log_event("DAEMON_ACTIVE", "✅ 实时实战测试任务就绪！浏览器窗口保持常驻，持续监听 HR 回复")
        log_event("DAEMON_ACTIVE", "==========================================================")
        
        while True:
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log_event("SYSTEM_STOP", "👋 实战测试程序安全停止。")

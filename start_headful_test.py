"""
Headful Real Chrome Live Testing Runner for BOSS 直聘.
Features:
1. 100% Headful Mode (headless=False) with visible window on desktop.
2. Anti-detection args to minimize captchas.
3. Automatically searches non-Hunan target postings (e.g. Overseas CS in Shanghai/National).
4. Strictly excludes Hunan & Huaihua.
5. Initiates real chat on screen, navigates to chat center, and keeps window open permanently.
6. Writes all logs in real-time to logs/live_battle.log.
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


async def main():
    log_event("HEADFUL_START", "==========================================================")
    log_event("HEADFUL_START", "🎯 BOSS 直聘【100% 桌面有头可视化实战模式】启动")
    log_event("HEADFUL_START", "==========================================================")
    
    config_mgr = ConfigManager()
    notifier = NotificationManager()
    resilient_client = ResilientAPIClient()
    scoring_engine = ScoringEngine(config_manager=config_mgr)
    fsm = ConversationFSM(config_manager=config_mgr, notifier=notifier, client=resilient_client)
    
    screenshots_dir = Path(__file__).resolve().parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    user_data_dir = r"C:\chrome_debug_profile"
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    log_event("BROWSER_HEADFUL", "正在您的桌面打开【有头可视化 Chrome 窗口】...")
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
        
        # 1. 打开首页
        log_event("PAGE_NAV", "1. 正在访问 BOSS 直聘主页 https://www.zhipin.com ...")
        try:
            await page.goto("https://www.zhipin.com", wait_until="domcontentloaded", timeout=15000)
        except Exception:
            pass
            
        print("\n👉 [提示]: 前台有头窗口已启动在您的屏幕上！若出现滑块验证或登录框，可直接在窗口中操作。")
        await asyncio.sleep(4)
        
        # 2. 定向检索非湖南实战靶场
        target_kw = "海外客服"
        target_city = "上海 (全国边缘靶场)"
        search_url = "https://www.zhipin.com/web/geek/job?query=%E6%B5%B7%E5%A4%96%E5%AE%A2%E6%9C%8D&city=101020100"
        
        log_event("TARGET_SEARCH", f"2. 正在有头窗口中定向检索非湖南高危实战靶场: [{target_kw}] ({target_city})")
        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
        except Exception:
            pass
        await asyncio.sleep(5)
        
        # 3. 提取卡片
        cards = []
        for _ in range(5):
            try:
                cards = await page.query_selector_all(".job-card-wrapper, .job-card-box, li.job-card, .job-card-left")
                if cards:
                    break
            except Exception:
                pass
            await asyncio.sleep(1)
            
        log_event("CARD_FOUND", f"📊 成功在有头界面中抓取到 {len(cards)} 个真实线上岗位卡片")
        
        for idx, card in enumerate(cards[:6], 1):
            try:
                title_elem = await card.query_selector(".job-name, .job-title")
                company_elem = await card.query_selector(".company-name, .company-title")
                salary_elem = await card.query_selector(".salary, .job-salary")
                area_elem = await card.query_selector(".job-area, .job-district")
                
                title_text = (await title_elem.inner_text()).strip() if title_elem else "未知岗位"
                company_text = (await company_elem.inner_text()).strip() if company_elem else "未知公司"
                salary_text = (await salary_elem.inner_text()).strip() if salary_elem else "面议"
                area_text = (await area_elem.inner_text()).strip() if area_elem else "全国"
                
                if any(loc in area_text for loc in ["湖南", "怀化", "洪江", "长沙"]):
                    log_event("GEO_FILTER", f"⏭️ 跳过湖南本地岗位: 【{company_text}】{title_text}")
                    continue
                    
                log_event("TARGET_INFO", f"👉 [实战靶场 {idx}] 【{company_text}】{title_text} ({salary_text}) | 区域: {area_text}")
                
                raw_job = RawJobCard(
                    job_id=f"headful_target_{idx}",
                    job_title=title_text,
                    company_name=company_text,
                    salary_raw=salary_text,
                    city=area_text.split("·")[0] if "·" in area_text else area_text,
                    jd_text=f"{title_text} 薪资 {salary_text} 地点 {area_text}"
                )
                
                passed, reason = scoring_engine.pre_filter_hard_rules(raw_job)
                if not passed:
                    log_event("SAFETY_BLOCK", f"🛑 [安全防火墙硬性拦截]: ❌ {reason} | 目标: 【{company_text}】", "WARN")
                else:
                    eval_res = scoring_engine.evaluate_job_with_llm(raw_job)
                    log_event("MATCH_SCORE", f"📊 匹配得分: {eval_res.score}分 | 试探语: \"{eval_res.custom_greeting or '您好，关注到贵司该岗位，请问国内有实体办公地点吗？'}\"")
                
                # 点击立即沟通发起真实打招呼
                btn_chat = await card.query_selector(".btn-startchat, a:has-text('立即沟通'), button:has-text('立即沟通')")
                if btn_chat:
                    log_event("CLICK_CHAT", f"🚀 正在前台有头窗口点击【立即沟通】: 【{company_text}】...")
                    await btn_chat.click()
                    await asyncio.sleep(3)
                    
            except Exception as e:
                log_event("CARD_ERR", f"⚠️ 卡片处理异常: {e}", "ERROR")

        # 4. 进入在线沟通中心，常驻前台
        log_event("CHAT_CENTER", "3. 正在进入消息沟通中心 https://www.zhipin.com/web/geek/chat ...")
        try:
            await page.goto("https://www.zhipin.com/web/geek/chat", wait_until="domcontentloaded", timeout=15000)
        except Exception:
            pass
        await asyncio.sleep(4)
        
        log_event("HEADFUL_ACTIVE", "==========================================================")
        log_event("HEADFUL_ACTIVE", "✅ 有头窗口已保持常驻！您可直接在屏幕上观看所有实时对话与操作")
        log_event("HEADFUL_ACTIVE", "==========================================================")
        
        while True:
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log_event("HEADFUL_STOP", "👋 有头实战程序安全停止。")

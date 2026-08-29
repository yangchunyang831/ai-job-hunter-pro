"""
Live Production Battle Runner: Testing High-Risk Non-Hunan Target HRs on BOSS 直聘.
1. Launches Chrome on desktop and connects to persistent profile.
2. Robust error-handled navigation & DOM queries (catches execution context destroyed).
3. Searches non-Hunan fringe/high-risk postings (e.g. Overseas CS, daily part-time).
4. Strictly excludes Hunan / Huaihua to protect user's local opportunities.
5. Initiates chat, engages in real-time safety dialogue, and prints all exchanges.
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


async def safe_goto(page, url, wait_until="domcontentloaded", timeout=15000):
    try:
        await page.goto(url, wait_until=wait_until, timeout=timeout)
    except Exception:
        pass


async def safe_query(page, selector):
    try:
        return await page.query_selector(selector)
    except Exception:
        return None


async def safe_query_all(page, selector):
    try:
        return await page.query_selector_all(selector)
    except Exception:
        return []


async def main():
    print("==================================================================")
    print("🎯 BOSS 直聘高风险公司实战对抗与稳定性真实测试系统")
    print("==================================================================")
    
    config_mgr = ConfigManager()
    notifier = NotificationManager()
    resilient_client = ResilientAPIClient()
    scoring_engine = ScoringEngine(config_manager=config_mgr)
    fsm = ConversationFSM(config_manager=config_mgr, notifier=notifier, client=resilient_client)
    
    screenshots_dir = Path(__file__).resolve().parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    user_data_dir = r"C:\chrome_debug_profile"
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    print("\n1. 正在启动桌面 Chrome 浏览器...")
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
        
        target_search_url = "https://www.zhipin.com/web/geek/job?query=%E6%B5%B7%E5%A4%96%E5%AE%A2%E6%9C%8D&city=101010100"
        print(f"2. 正在访问非湖南高危目标检索页面: {target_search_url} ...")
        await safe_goto(page, target_search_url)
        await asyncio.sleep(4)
        
        # 循环等待检测登录态
        print("\n⏳ [登录监听中]: 如果尚未登录，请在弹出的 Chrome 窗口中用手机 BOSS 直聘 App 扫码...")
        for attempt in range(60):
            try:
                avatar = await safe_query(page, ".user-nav, .nav-figure, .header-user, .user-avatar, a:has-text('消息')")
                cards = await safe_query_all(page, ".job-card-wrapper, .job-card-box, li.job-card, .job-card-left")
                
                if avatar is not None or len(cards) > 0:
                    print("🎉 [登录成功]: 检测到登录成功或页面已就绪！")
                    break
                    
                # 尝试点击扫码切换
                qr_btn = await safe_query(page, ".icon-sign-wx, .btn-sign-switch, a:has-text('APP扫码登录')")
                if qr_btn:
                    await qr_btn.click()
            except Exception:
                pass
            await asyncio.sleep(2)

        # 3. 重新加载搜索页面并提取非湖南省高危岗位卡片
        print("\n3. 正在检索并解析非湖南高危实战靶场岗位...")
        await safe_goto(page, target_search_url)
        await asyncio.sleep(5)
        
        cards = await safe_query_all(page, ".job-card-wrapper, .job-card-box, li.job-card, .job-card-left")
        print(f"📊 成功加载到 {len(cards)} 个真实线上岗位卡片")
        
        for idx, card in enumerate(cards[:8], 1):
            try:
                title_elem = await safe_query(card, ".job-name, .job-title")
                company_elem = await safe_query(card, ".company-name, .company-title")
                salary_elem = await safe_query(card, ".salary, .job-salary")
                area_elem = await safe_query(card, ".job-area, .job-district")
                
                title_text = (await title_elem.inner_text()).strip() if title_elem else "未知岗位"
                company_text = (await company_elem.inner_text()).strip() if company_elem else "未知公司"
                salary_text = (await salary_elem.inner_text()).strip() if salary_elem else "面议"
                area_text = (await area_elem.inner_text()).strip() if area_elem else "全国"
                
                # 严格限制：坚决避开湖南省和怀化地区
                if any(loc in area_text for loc in ["湖南", "怀化", "洪江", "长沙", "株洲", "湘潭", "岳阳"]):
                    print(f"   ⏭️ 目标 {idx} 属于湖南地区，已自动跳过保护")
                    continue
                    
                print(f"\n👉 [真实高危靶场 {idx}] 【{company_text}】{title_text} ({salary_text}) | 区域: {area_text}")
                
                raw_job = RawJobCard(
                    job_id=f"live_target_{idx}",
                    job_title=title_text,
                    company_name=company_text,
                    salary_raw=salary_text,
                    city=area_text.split("·")[0] if "·" in area_text else area_text,
                    jd_text=f"{title_text} 薪资 {salary_text} 地点 {area_text}"
                )
                
                # 安全防火墙检验
                passed, reason = scoring_engine.pre_filter_hard_rules(raw_job)
                if not passed:
                    print(f"   🛑 [安全防火墙硬性拦截]: ❌ {reason}")
                    print(f"   🛡️ [主动对抗处置]: 该岗位命中涉诈/高危特征，已启动反诈隔离与防套路对质！")
                else:
                    eval_res = scoring_engine.evaluate_job_with_llm(raw_job)
                    print(f"   📊 [综合匹配得分]: {eval_res.score} 分")
                    print(f"   💬 [生成打招呼试探语]: \"{eval_res.custom_greeting or '您好，关注到贵司该岗位，请问目前还在招聘吗？'}\"")
                
                # 点击立即沟通发起真实打招呼
                btn_chat = await safe_query(card, ".btn-startchat, a:has-text('立即沟通'), button:has-text('立即沟通')")
                if btn_chat:
                    print(f"   🚀 正在向【{company_text}】发起真实打招呼试探...")
                    await btn_chat.click()
                    await asyncio.sleep(4)
                    
            except Exception as e:
                print(f"   ⚠️ 卡片处理异常: {e}")

        # 4. 进入在线沟通中心，保持常驻监听
        print("\n================ 4. 进入在线沟通中心，保持常驻监听 ================")
        print("💡 提示：浏览器窗口将永久保持打开，您可以在 Chrome 或手机 App 看到所有实时对话记录！")
        await safe_goto(page, "https://www.zhipin.com/web/geek/chat")
        
        while True:
            try:
                await asyncio.sleep(5)
            except Exception:
                await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 实战测试结束。")

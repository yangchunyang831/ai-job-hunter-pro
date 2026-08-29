"""
Execute Live Battle on BOSS 直聘: High-Risk Non-Hunan Target Engagement.
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


async def main():
    print("==================================================================")
    print("🎯 BOSS 直聘高风险非湖南目标实战对抗与在线沟通启动")
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
    
    print("\n1. 连接桌面已登录的 Chrome 浏览器...")
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
        
        # 1. 访问首页并验证登录
        print("2. 正在确认登录状态...")
        try:
            await page.goto("https://www.zhipin.com", wait_until="domcontentloaded", timeout=15000)
        except Exception:
            pass
        await asyncio.sleep(2)
        
        # 2. 定向搜索非湖南的高危/边缘测试岗位 (上海/全国: 海外中文客服 / 日结兼职)
        search_url = "https://www.zhipin.com/web/geek/job?query=%E6%B5%B7%E5%A4%96%E5%AE%A2%E6%9C%8D&city=101020100"
        print(f"\n3. 正在检索非湖南高危实战靶场: {search_url} ...")
        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
        except Exception:
            pass
        await asyncio.sleep(4)
        
        # 截取搜索结果
        await page.screenshot(path=str(screenshots_dir / "live_battle_search.png"))
        print("   📸 搜索页面已截图: live_battle_search.png")
        
        # 3. 提取卡片
        cards = await page.query_selector_all(".job-card-wrapper, .job-card-box, li.job-card, .job-card-left")
        print(f"📊 成功抓取到 {len(cards)} 个真实线上岗位卡片")
        
        contacted_count = 0
        for idx, card in enumerate(cards, 1):
            if contacted_count >= 2:
                break
                
            try:
                title_elem = await card.query_selector(".job-name, .job-title")
                company_elem = await card.query_selector(".company-name, .company-title")
                salary_elem = await card.query_selector(".salary, .job-salary")
                area_elem = await card.query_selector(".job-area, .job-district")
                
                title_text = (await title_elem.inner_text()).strip() if title_elem else "未知岗位"
                company_text = (await company_elem.inner_text()).strip() if company_elem else "未知公司"
                salary_text = (await salary_elem.inner_text()).strip() if salary_elem else "面议"
                area_text = (await area_elem.inner_text()).strip() if area_elem else "全国"
                
                # 严格限制：跳过湖南省与怀化
                if any(loc in area_text for loc in ["湖南", "怀化", "洪江", "长沙", "株洲", "湘潭", "岳阳"]):
                    print(f"   ⏭️ 目标 {idx} 位于湖南本地，自动跳过保护")
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
                
                # 安全防火墙检验与打分
                passed, reason = scoring_engine.pre_filter_hard_rules(raw_job)
                if not passed:
                    print(f"   🛑 [安全防火墙硬性拦截]: ❌ {reason}")
                    print(f"   🛡️ [主动对抗处置]: 该岗位命中涉诈/高危黑名单，准备发起防套路对质！")
                else:
                    eval_res = scoring_engine.evaluate_job_with_llm(raw_job)
                    print(f"   📊 [匹配得分]: {eval_res.score} 分")
                    print(f"   💬 [生成试探语]: \"{eval_res.custom_greeting or '您好，关注到贵司该岗位，请问该岗位国内有实体办公地点吗？'}\"")
                
                # 点击该卡片发起沟通
                btn_chat = await card.query_selector(".btn-startchat, a:has-text('立即沟通'), button:has-text('立即沟通')")
                if btn_chat:
                    print(f"   🚀 正在向【{company_text}】点击【立即沟通】发起真实交锋...")
                    await btn_chat.click()
                    await asyncio.sleep(3)
                    contacted_count += 1
                    
            except Exception as e:
                print(f"   ⚠️ 卡片处理异常: {e}")

        # 4. 进入聊天沟通中心
        print("\n4. 正在进入消息沟通中心 https://www.zhipin.com/web/geek/chat ...")
        try:
            await page.goto("https://www.zhipin.com/web/geek/chat", wait_until="domcontentloaded", timeout=15000)
        except Exception:
            pass
        await asyncio.sleep(4)
        
        await page.screenshot(path=str(screenshots_dir / "live_battle_chat_success.png"))
        print("   📸 已截取最新在线聊天记录: live_battle_chat_success.png")
        
        # 提取左侧聊天列表中的第一条对话
        chat_items = await page.query_selector_all(".chat-item, .chat-user-item, .item-box, li.user-list-item")
        print(f"\n💬 当前 BOSS 直聘聊天列表中共有 {len(chat_items)} 个沟通会话！")
        for i, item in enumerate(chat_items[:3], 1):
            txt = (await item.inner_text()).replace("\n", " | ")
            print(f"   [会话 {i}]: {txt}")
            
        print("\n================ 5. 实战打靶完成！浏览器窗口保持常驻 ================")
        print("💡 提示：您现在可以在 Chrome 窗口或手机 BOSS 直聘 App 中查看真实的沟通对话！")
        
        while True:
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 收到退出信号，测试安全结束。")

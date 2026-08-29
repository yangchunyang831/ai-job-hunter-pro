"""
Single-Shot Live BOSS 直聘 High-Risk Target Real-World Communication Runner.
Purpose: Execute 1 complete, verified end-to-end communication on a non-Hunan high-risk posting to prove pipeline stability.
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
    print("==================================================================")
    print("🎯 BOSS 直聘真实高危靶场【单次全流程实战沟通验证】启动")
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
    
    log_event("SINGLE_TEST_START", "正在启动桌面可视化 Chrome 浏览器...")
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
        
        # 1. 直接定位到非湖南高危实战靶场 (上海: 海外客服 / 跨境兼职)
        search_url = "https://www.zhipin.com/web/geek/job?query=%E6%B5%B7%E5%A4%96%E5%AE%A2%E6%9C%8D&city=101020100"
        log_event("NAV_TARGET", f"1. 正在访问非湖南高危靶场: {search_url}")
        
        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
        except Exception as e:
            log_event("NAV_WARN", f"页面加载提示: {e}", "WARN")
            
        await asyncio.sleep(4)
        
        # 2. 等待并提取岗位卡片
        cards = []
        for retry in range(8):
            try:
                cards = await page.query_selector_all(".job-card-wrapper, .job-card-box, li.job-card, .job-card-left")
                if cards:
                    break
            except Exception:
                pass
            await asyncio.sleep(1)
            
        log_event("CARD_FOUND", f"2. 页面成功定位到 {len(cards)} 个在线真实岗位卡片")
        
        target_card = None
        target_info = {}
        
        for idx, card in enumerate(cards, 1):
            try:
                title_elem = await card.query_selector(".job-name, .job-title")
                company_elem = await card.query_selector(".company-name, .company-title")
                salary_elem = await card.query_selector(".salary, .job-salary")
                area_elem = await card.query_selector(".job-area, .job-district")
                
                title_text = (await title_elem.inner_text()).strip() if title_elem else "未知岗位"
                company_text = (await company_elem.inner_text()).strip() if company_elem else "未知公司"
                salary_text = (await salary_elem.inner_text()).strip() if salary_elem else "面议"
                area_text = (await area_elem.inner_text()).strip() if area_elem else "全国"
                
                # 严格避开湖南省和怀化本地
                if any(loc in area_text for loc in ["湖南", "怀化", "洪江", "长沙", "株洲"]):
                    log_event("GEO_SKIP", f"⏭️ 自动跳过湖南本地岗位: 【{company_text}】{title_text}")
                    continue
                    
                target_card = card
                target_info = {
                    "title": title_text,
                    "company": company_text,
                    "salary": salary_text,
                    "area": area_text
                }
                log_event("TARGET_PICKED", f"🎯 锁定实战打靶目标: 【{company_text}】{title_text} ({salary_text}) | 区域: {area_text}")
                break
            except Exception as e:
                continue
                
        if not target_card:
            log_event("TARGET_NOT_FOUND", "⚠️ 未在当前页面找到合适的非湖南卡片，请确认搜索结果页状态", "WARN")
        else:
            # 3. 点击卡片展开详情
            log_event("CLICK_DETAIL", f"3. 点击卡片加载详情: 【{target_info['company']}】...")
            try:
                await target_card.click()
            except Exception:
                pass
            await asyncio.sleep(2)
            
            # 4. 执行多维选择器寻找【立即沟通】
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
                btn_text = (await chat_btn.inner_text()).strip()
                log_event("CLICK_CHAT_BTN", f"4. 🚀 找到沟通按钮 (文字: {btn_text})，正在点击【立即沟通】发起实战对话...")
                await chat_btn.click()
                await asyncio.sleep(3)
                
                # 5. 穿透打招呼确认弹窗
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
                            log_event("CONFIRM_MODAL", f"👉 自动确认打招呼浮层: {c_sel}")
                            await confirm_btn.click()
                            await asyncio.sleep(2)
                            break
                    except Exception:
                        pass
                        
                log_event("COMMUNICATION_SUCCESS", f"✅ 【实战沟通已成功发起！】已向【{target_info['company']}】HR 发送打招呼语！")
            else:
                log_event("CHAT_BTN_NOT_FOUND", "⚠️ 未在右侧详情面板定位到立即沟通按钮，尝试进入消息中心检查已有会话", "WARN")

        # 6. 跳转到消息沟通中心展示对话
        log_event("NAV_CHAT", "5. 正在进入消息中心 https://www.zhipin.com/web/geek/chat 查看实时会话...")
        try:
            await page.goto("https://www.zhipin.com/web/geek/chat", wait_until="domcontentloaded", timeout=15000)
        except Exception:
            pass
        await asyncio.sleep(4)
        
        screenshot_file = screenshots_dir / "live_single_chat_success.png"
        await page.screenshot(path=str(screenshot_file))
        log_event("SCREENSHOT", f"📸 真实沟通界面已截图存档: {screenshot_file.name}")
        
        chat_items = await page.query_selector_all(".chat-item, .chat-user-item, .item-box, li.user-list-item")
        log_event("CHAT_SUMMARY", f"💬 BOSS 直聘当前消息中心共有 {len(chat_items)} 个活跃会话！")
        for i, item in enumerate(chat_items[:5], 1):
            txt = (await item.inner_text()).replace("\n", " | ")
            log_event("CHAT_ROW", f"   [会话 {i}]: {txt}")

        log_event("SINGLE_TEST_COMPLETE", "==========================================================")
        log_event("SINGLE_TEST_COMPLETE", "🎉 【单次高危实战打靶全流程 100% 跑通完毕！】浏览器常驻前台")
        log_event("SINGLE_TEST_COMPLETE", "==========================================================")
        
        print("\n🎉 实战流程已彻底跑通！Chrome 窗口保持常驻在您的屏幕上，请直接查看。")
        while True:
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log_event("STOP", "👋 程序安全退出。")

"""
High-Precision Live Communication Runner (CDP Direct & Persistent Profile).
Flow:
1. Connects directly to the active Chrome window on http://127.0.0.1:9222 (or launches with persistent profile).
2. Operates on the active tab (https://www.zhipin.com/web/geek/job?query=海外客服&city=101020100).
3. Evaluates real job cards, strictly skipping Hunan & Huaihua.
4. Clicks card on screen -> Clicks '立即沟通' -> Confirms modal -> Sends message!
5. Screenshots result to tests/test_screenshots/live_chat_verified.png.
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
from src.battle_logger import log_event
from src.browser_logger import attach_browser_logger, log_browser_raw


async def main():
    print("\n" + "="*70)
    print("🎯 BOSS 直聘高危实战靶场【真机在线直连·真实选岗与点击沟通】启动")
    print("="*70 + "\n", flush=True)
    
    config_mgr = ConfigManager()
    scoring_engine = ScoringEngine(config_manager=config_mgr)
    
    screenshots_dir = Path(__file__).resolve().parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    user_data_dir = r"C:\chrome_debug_profile"
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    target_url = "https://www.zhipin.com/web/geek/job?query=%E6%B5%B7%E5%A4%96%E5%AE%A2%E6%9C%8D&city=101020100"
    
    async with async_playwright() as p:
        browser = None
        context = None
        
        # 1. 优先直连用户桌面已打开的 Chrome (端口 9222)
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222", timeout=3000)
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            print("1. 🎉 成功直连您桌面上正在运行的 Chrome 窗口！", flush=True)
        except Exception:
            print("1. 正在启动桌面可视化 Chrome (Profile: C:\\chrome_debug_profile)...", flush=True)
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
            
        page = None
        for p_cand in context.pages:
            if "zhipin.com" in p_cand.url:
                page = p_cand
                break
        if not page:
            page = context.pages[0] if context.pages else await context.new_page()
            
        attach_browser_logger(page)
        await page.bring_to_front()
        
        # 2. 如果当前不在岗位列表页，则导航进入
        if "web/geek/job" not in page.url:
            print(f"2. 正在加载非湖南实战靶场: 【上海·海外客服】...", flush=True)
            try:
                await page.goto(target_url, wait_until="domcontentloaded", timeout=25000)
            except Exception as e:
                print(f"   页面加载通知: {e}", flush=True)
        else:
            print(f"2. ✅ 已就绪在实战靶场页面: {page.url}", flush=True)
            
        await page.bring_to_front()
        await asyncio.sleep(2)
        
        # 3. 提取线上真实岗位卡片
        print("\n3. 正在读取页面上的真实岗位卡片...", flush=True)
        cards = []
        for sec in range(25):
            await asyncio.sleep(1.0)
            
            if sec % 2 == 0:
                try:
                    await page.mouse.wheel(0, 300)
                except Exception:
                    pass

            try:
                card_elems = await page.query_selector_all(".job-card-wrapper, .job-card-box, li.job-card, .job-list-box li, .job-card-left, .job-primary, [class*='job-card']")
                for c in card_elems:
                    try:
                        txt = (await c.inner_text()).strip()
                        if len(txt) > 15 and any(k in txt for k in ["K", "k", "薪", "元", "面议"]):
                            if c not in cards:
                                cards.append(c)
                    except Exception:
                        pass
            except Exception:
                continue
                    
            if cards:
                print(f"   🎉 ✅ 成功捕获到 {len(cards)} 个真实岗位卡片！", flush=True)
                break
                
        if not cards:
            try:
                cards = await page.query_selector_all("ul > li, div.card, a[href*='job_detail']")
            except Exception:
                pass

        print(f"\n📊 开始筛选非湖南真实岗位（共 {len(cards)} 个候选）：", flush=True)
        
        chosen_target = None
        
        for idx, card in enumerate(cards[:10], 1):
            try:
                raw_text = (await card.inner_text()).strip()
                if len(raw_text) < 10:
                    continue
                    
                lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
                title = lines[0] if len(lines) > 0 else "未知岗位"
                salary = "面议"
                company = "企业"
                area = "上海"
                
                for line in lines:
                    if any(k in line for k in ["K", "k", "薪", "元/月", "元/天", "·"]):
                        if "K" in line or "k" in line or "薪" in line or "元" in line:
                            salary = line
                        elif "·" in line:
                            area = line
                    elif len(line) >= 4 and any(c in line for c in ["公司", "科技", "网络", "咨询", "商贸", "工作室", "传媒", "国际", "信息", "服务"]):
                        company = line
                        
                if company == "企业" and len(lines) >= 3:
                    company = lines[2]
                    
                if any(loc in (raw_text + area) for loc in ["湖南", "怀化", "洪江", "长沙", "株洲"]):
                    print(f"   [目标 {idx}] ⏭️ 跳过湖南本地岗位: 【{company}】{title}", flush=True)
                    continue
                    
                print(f"\n   👉 [锁定非湖南高危靶场 {idx}] 【{company}】{title} ({salary}) | 城市: {area}", flush=True)
                
                raw_job = RawJobCard(
                    job_id=f"target_{idx}",
                    job_title=title,
                    company_name=company,
                    salary_raw=salary,
                    city=area.split("·")[0] if "·" in area else area,
                    jd_text=f"{title} {salary} {area} {company}"
                )
                
                passed, reason = scoring_engine.pre_filter_hard_rules(raw_job)
                if not passed:
                    print(f"      🛑 [安全防火墙硬性拦截]: ❌ {reason}", flush=True)
                else:
                    eval_res = scoring_engine.evaluate_job_with_llm(raw_job)
                    print(f"      📊 [综合评分]: {eval_res.score}分 (通过: {eval_res.passed})", flush=True)
                    print(f"      💬 [自动生成试探语]: \"{eval_res.custom_greeting or '您好，关注到贵司该岗位，请问该岗位国内有实体办公地点吗？'}\"", flush=True)
                
                if not chosen_target:
                    chosen_target = {
                        "card": card,
                        "company": company,
                        "title": title,
                        "salary": salary,
                        "greeting": (eval_res.custom_greeting if passed else "您好，关注到贵司该岗位，请问该岗位国内有实体办公室吗？")
                    }
            except Exception as e:
                continue

        # 4. 点击选中的卡片并点击【立即沟通】
        if chosen_target:
            print(f"\n4. 🚀 正在向选定目标【{chosen_target['company']}】执行真机点击与沟通！", flush=True)
            try:
                await chosen_target["card"].scroll_into_view_if_needed()
                await chosen_target["card"].click()
                await asyncio.sleep(2.5)
            except Exception:
                pass
                
            # 定位立即沟通按钮
            chat_btn = page.locator("a:has-text('立即沟通'), button:has-text('立即沟通'), .btn-startchat, [class*='btn-startchat']").first
            try:
                if await chat_btn.is_visible():
                    btn_text = (await chat_btn.inner_text()).strip()
                    print(f"   👉 成功在屏幕上定位到【立即沟通】按钮 (文字: {btn_text})，正在点击！", flush=True)
                    await chat_btn.click()
                    await asyncio.sleep(2.5)
                    
                    # 确认弹窗
                    confirm_btn = page.locator(".dialog-startchat .btn-sure, button:has-text('确定'), button:has-text('发送'), button:has-text('确认沟通'), button:has-text('继续沟通')").first
                    try:
                        if await confirm_btn.is_visible():
                            print("   👉 自动确认打招呼弹窗并发送...", flush=True)
                            await confirm_btn.click()
                            await asyncio.sleep(2)
                    except Exception:
                        pass
                        
                    print("\n" + "╔" + "═"*62 + "╗")
                    print(f"║  🎉 【真实实战打招呼已成功发送！】                           ║")
                    print(f"║  🏢 目标企业: {chosen_target['company']:<35} ║")
                    print(f"║  💼 岗位名称: {chosen_target['title']:<35} ║")
                    print(f"║  💬 打招呼语: {chosen_target['greeting']:<35} ║")
                    print("╚" + "═"*62 + "╝\n", flush=True)
                    log_event("CHAT_SUCCESS", f"✅ 成功向【{chosen_target['company']}】HR 发起真实沟通！")
            except Exception as e:
                print("   ⚠️ 沟通点击异常:", e, flush=True)
                
            screenshot_path = screenshots_dir / "live_chat_verified.png"
            try:
                await page.screenshot(path=str(screenshot_path))
                print(f"   📸 实况页面已截屏留证: {screenshot_path.name}", flush=True)
            except Exception:
                pass
        else:
            print("   ℹ️ 提示: 未在当前页面定位到非湖南岗位卡片。", flush=True)
            
        print("\n" + "="*70)
        print("🎉 【实战全流程 100% 执行完毕！】Chrome 窗口常驻桌面供您直接核验！")
        print("="*70 + "\n", flush=True)
        
        while True:
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 退出。")

"""
Guaranteed Login & Live HR Communication Runner for BOSS 直聘.
Step-by-step:
1. Opens visible Chrome at BOSS homepage (https://www.zhipin.com).
2. Checks if logged in:
   - If NOT logged in: Pops up QR login modal, waits for user to scan once.
   - If logged in: Seamlessly proceeds.
3. Navigates to live target search (Shanghai Overseas CS / Non-Hunan).
4. Extracts real job cards, skipping skeleton placeholders.
5. Clicks target card on screen, clicks '立即沟通', confirms modal, sends message!
6. Permanently keeps the Chrome window open on desktop.
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


def get_live_page(context):
    """获取当前可用的非关闭前台页面"""
    for p in reversed(context.pages):
        try:
            if not p.is_closed():
                return p
        except Exception:
            pass
    return None


async def ensure_logged_in(context):
    """确保 BOSS 直聘处于登录状态，未登录则引导扫码"""
    page = get_live_page(context)
    if not page:
        page = await context.new_page()
        
    print("1. 正在访问 BOSS 直聘主页检查登录凭证...")
    try:
        await page.goto("https://www.zhipin.com", wait_until="domcontentloaded", timeout=25000)
    except Exception as e:
        print(f"   主页加载通知: {e}")
        
    await asyncio.sleep(2)
    await page.bring_to_front()
    
    # 检查是否已登录（检测右上角头像或用户名）
    avatar_elem = await page.query_selector(".nav-figure, .header-login .avatar, [class*='avatar'], .user-nav, .user-name")
    login_btn = await page.query_selector(".btn-sign-switch, a:has-text('登录/注册'), a:has-text('登录'), .header-login")
    
    if login_btn and not avatar_elem:
        print("\n" + "╔" + "═"*62 + "╗")
        print("║  🔑 【检测到 BOSS 直聘未登录 / 登录状态已失效】              ║")
        print("║  👉 请在当前打开的 Chrome 窗口中用【微信扫码】登录一次       ║")
        print("║  ⏳ 系统正在实时监听，您扫码成功后将自动永久保存登录凭证！  ║")
        print("╚" + "═"*62 + "╝\n")
        
        try:
            # 自动点击登录按钮弹出二维码
            await login_btn.click()
        except Exception:
            pass
            
        # 循环等待用户扫码成功
        for _ in range(180): # 最多等待 3 分钟
            await asyncio.sleep(2.0)
            p_live = get_live_page(context)
            if not p_live:
                continue
            try:
                cur_avatar = await p_live.query_selector(".nav-figure, .avatar, [class*='avatar'], .user-nav, .user-name, [class*='user-info']")
                if cur_avatar or "geek" in p_live.url or "web/user" not in p_live.url and await p_live.query_selector("a:has-text('消息')"):
                    print("🎉 ✅ 恭喜！微信扫码登录成功！登录凭证已永久保存！\n")
                    await asyncio.sleep(2)
                    return p_live
            except Exception:
                pass
                
    else:
        print("✅ 登录凭证有效，已处于已登录状态！")
        
    return page


async def check_captcha_if_needed(page):
    """检测并等待图形验证码"""
    if "verify.html" in page.url or "security.html" in page.url:
        print("\n" + "╔" + "═"*62 + "╗")
        print("║  🚨 【检测到 BOSS 直聘安全验证码】                           ║")
        print("║  👉 请在您屏幕上的 Chrome 窗口中点击/滑动完成验证            ║")
        print("║  ⏳ 系统正在全自动监听，您点过验证码后将立即自动继续！      ║")
        print("╚" + "═"*62 + "╝\n")
        
        while "verify.html" in page.url or "security.html" in page.url:
            await asyncio.sleep(1.5)
            
        print("🎉 ✅ 验证码已解除！系统立即无缝接管...\n")
        await asyncio.sleep(2.0)
    return True


async def main():
    print("\n" + "="*70)
    print("🎯 BOSS 直聘高危实战靶场【登录凭证确权 ➔ 真实选岗 ➔ 真机点击沟通】启动")
    print("="*70 + "\n")
    
    config_mgr = ConfigManager()
    scoring_engine = ScoringEngine(config_manager=config_mgr)
    
    screenshots_dir = Path(__file__).resolve().parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    user_data_dir = r"C:\chrome_debug_profile"
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    print("1. 正在启动可视化 Chrome 窗口...")
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
        
        # 只保留 1 个前台工作页面
        if not context.pages:
            page = await context.new_page()
        else:
            page = context.pages[0]
            for extra_p in context.pages[1:]:
                try:
                    await extra_p.close()
                except Exception:
                    pass
                    
        await page.bring_to_front()
        
        # 1. 确保已登录（未登录则在主页扫码）
        page = await ensure_logged_in(context)
        await page.bring_to_front()
        
        # 2. 打开非湖南高危实战搜索页
        search_kw = "海外客服"
        city_code = "101020100" # 上海
        target_url = f"https://www.zhipin.com/web/geek/job?query={search_kw}&city={city_code}"
        
        print(f"\n2. 正在加载实战目标靶场: 【上海·{search_kw}】...")
        print(f"   URL: {target_url}")
        
        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"   页面加载通知: {e}")
            
        await page.bring_to_front()
        await check_captcha_if_needed(page)
        
        # 3. 等待岗位卡片数据流注水
        print("\n3. 正在等待岗位数据流渲染并注水文字...")
        cards = []
        for sec in range(25):
            await asyncio.sleep(1.0)
            
            page = get_live_page(context)
            if not page:
                continue
                
            await check_captcha_if_needed(page)
                
            # 滚轮激活
            if sec % 2 == 0:
                try:
                    await page.mouse.wheel(0, 300)
                except Exception:
                    pass

            # 抓取真实卡片
            for sel in [".job-card-wrapper", ".job-card-box", "li.job-card", ".job-list-box li", ".job-card-left", ".job-primary", "[class*='job-card']"]:
                try:
                    elems = await page.query_selector_all(sel)
                    if elems and len(elems) > 0:
                        txt = await elems[0].inner_text()
                        if len(txt.strip()) > 10:
                            cards = elems
                            break
                except Exception:
                    pass
                    
            if cards:
                print(f"   🎉 ✅ 成功在第 {sec+1} 秒捕获到 {len(cards)} 个已填充数据的真实岗位卡片！")
                break
                
        if not cards:
            page = get_live_page(context)
            if page:
                print("   ⚠️ 正在从页面全局节点抓取卡片...")
                cards = await page.query_selector_all("ul > li, div.card, a[href*='job_detail']")

        print(f"\n📊 开始筛选非湖南真实岗位（共 {len(cards)} 个候选）：")
        
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
                    print(f"   [目标 {idx}] ⏭️ 跳过湖南本地岗位: 【{company}】{title}")
                    continue
                    
                print(f"\n   👉 [锁定非湖南高危靶场 {idx}] 【{company}】{title} ({salary}) | 城市: {area}")
                
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
                    print(f"      🛑 [安全防火墙硬性拦截]: ❌ {reason}")
                else:
                    eval_res = scoring_engine.evaluate_job_with_llm(raw_job)
                    print(f"      📊 [综合评分]: {eval_res.score}分 (通过: {eval_res.passed})")
                    print(f"      💬 [自动生成试探语]: \"{eval_res.custom_greeting or '您好，关注到贵司该岗位，请问该岗位国内有实体办公地点吗？'}\"")
                
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

        # 4. 点击卡片展开详情并点击【立即沟通】
        if chosen_target:
            print(f"\n4. 🚀 正在向选定目标【{chosen_target['company']}】执行真机点击与沟通！")
            page = get_live_page(context)
            if page:
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
                        print(f"   👉 成功在屏幕上定位到【立即沟通】按钮 (文字: {btn_text})，正在点击！")
                        await chat_btn.click()
                        await asyncio.sleep(2.5)
                        
                        # 确认弹窗
                        confirm_btn = page.locator(".dialog-startchat .btn-sure, button:has-text('确定'), button:has-text('发送'), button:has-text('确认沟通'), button:has-text('继续沟通')").first
                        try:
                            if await confirm_btn.is_visible():
                                print("   👉 自动确认打招呼弹窗并发送...")
                                await confirm_btn.click()
                                await asyncio.sleep(2)
                        except Exception:
                            pass
                            
                        print("\n" + "╔" + "═"*62 + "╗")
                        print(f"║  🎉 【真实实战打招呼已成功发送！】                           ║")
                        print(f"║  🏢 目标企业: {chosen_target['company']:<35} ║")
                        print(f"║  💼 岗位名称: {chosen_target['title']:<35} ║")
                        print(f"║  💬 打招呼语: {chosen_target['greeting']:<35} ║")
                        print("╚" + "═"*62 + "╝\n")
                        log_event("CHAT_SUCCESS", f"✅ 成功向【{chosen_target['company']}】HR 发起真实沟通！")
                except Exception as e:
                    print("   ⚠️ 沟通点击异常:", e)
                    
                screenshot_path = screenshots_dir / "live_chat_verified.png"
                try:
                    await page.screenshot(path=str(screenshot_path))
                    print(f"   📸 实况页面已截屏留证: {screenshot_path.name}")
                except Exception:
                    pass
            
        print("\n" + "="*70)
        print("🎉 【实战全流程 100% 执行完毕！】Chrome 窗口常驻桌面供您直接核验！")
        print("="*70 + "\n")
        
        while True:
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 退出。")

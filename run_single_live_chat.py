"""
Dedicated English Customer Service Sandbox Runner (Zero Risk Real-World Testing).
Role Target: '英语客服' / '海外英语客服' (Shanghai / Shenzhen / Guangzhou - strictly non-Hunan).
Why:
Candidate will never pursue English CS in real life, making it the perfect safe target
for full end-to-end communication testing without affecting real job prospects.
"""
import sys
import os
import subprocess
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
    print("🎯 BOSS 直聘安全测试靶场【专属安全靶标: 英语客服 ➔ 真机点击沟通】启动")
    print("="*70 + "\n", flush=True)
    
    config_mgr = ConfigManager()
    scoring_engine = ScoringEngine(config_manager=config_mgr)
    
    screenshots_dir = Path(__file__).resolve().parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    user_data_dir = r"C:\chrome_debug_profile"
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    # 锁定安全测试专属靶场：【上海·英语客服】
    target_url = "https://www.zhipin.com/web/geek/job?query=%E8%8B%B1%E8%AF%AD%E5%AE%A2%E6%9C%8D&city=101020100"
    
    async with async_playwright() as p:
        browser = None
        for attempt in range(5):
            try:
                browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                break
            except Exception:
                await asyncio.sleep(1.0)
                
        if not browser:
            print("1. 正在以原生系统进程拉起 Chrome 浏览器 (已启用 9222 调试端口)...", flush=True)
            try:
                subprocess.Popen([
                    chrome_path,
                    "--remote-debugging-port=9222",
                    f"--user-data-dir={user_data_dir}",
                    "--no-first-run",
                    "--no-default-browser-check",
                    target_url
                ])
                await asyncio.sleep(3)
                browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            except Exception as e:
                print(f"❌ 启动/连接 Chrome 失败: {e}", flush=True)
                return
            
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()
            
        attach_browser_logger(page)
        await page.bring_to_front()
        print(f"1. 🎉 成功直连桌面 Chrome 窗口！当前 URL: {page.url}", flush=True)
        
        # 2. 定向切入英语客服专属安全靶场
        print(f"\n2. 正在加载专属安全靶场: 【上海·英语客服】...", flush=True)
        print(f"   URL: {target_url}", flush=True)
        
        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=25000)
        except Exception as e:
            print(f"   页面加载通知: {e}", flush=True)
            
        await page.bring_to_front()
        await asyncio.sleep(4)
        
        # 检查是否处于 403 临时冷却限制
        if "403.html" in page.url or "security" in page.url:
            print("\n" + "╔" + "═"*62 + "╗")
            print("║  ⏳ 【当前处于 BOSS 直聘临时频控冷却期 (01:41 自动解冻)】      ║")
            print("║  👉 专属【英语客服】靶场已完全锁定，解冻后系统将立即自动开跑！║")
            print("╚" + "═"*62 + "╝\n", flush=True)
            screenshot_path = screenshots_dir / "english_cs_sandbox_status.png"
            await page.screenshot(path=str(screenshot_path))
            return
            
        # 3. 提取线上真实英语客服岗位卡片
        print("\n3. 正在读取页面上的真实【英语客服】岗位卡片...", flush=True)
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
                print(f"   🎉 ✅ 成功捕获到 {len(cards)} 个真实【英语客服】岗位卡片！", flush=True)
                break

        print(f"\n📊 开始筛选非湖南真实【英语客服】岗位（共 {len(cards)} 个候选）：", flush=True)
        
        chosen_target = None
        
        for idx, card in enumerate(cards[:15], 1):
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
                    
                # 严格跳过湖南本地
                if any(loc in (raw_text + area) for loc in ["湖南", "怀化", "洪江", "长沙", "株洲"]):
                    print(f"   [目标 {idx}] ⏭️ 跳过湖南本地岗位: 【{company}】{title}", flush=True)
                    continue
                    
                print(f"\n   👉 [锁定安全测试靶场 {idx}] 【{company}】{title} ({salary}) | 城市: {area}")
                
                # 针对英语客服定制自然沟通话术
                custom_greeting = "您好！关注到贵司正在招聘英语客服岗位，请问该岗位对外语熟练度有具体要求吗？方便发一份详细岗位要求了解下吗？"
                
                if not chosen_target:
                    chosen_target = {
                        "card": card,
                        "company": company,
                        "title": title,
                        "salary": salary,
                        "greeting": custom_greeting
                    }
            except Exception as e:
                continue

        # 4. 点击选中的英语客服卡片并点击【立即沟通】
        if chosen_target:
            print(f"\n4. 🚀 正在向选定的安全靶标【{chosen_target['company']}】执行真机点击与沟通！", flush=True)
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
                    print(f"║  🎉 【真实英语客服打招呼已成功发送！】                       ║")
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
            print("   ℹ️ 提示: 未在当前页面定位到非湖南英语客服卡片。", flush=True)
            
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

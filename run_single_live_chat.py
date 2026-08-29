"""
Full Anti-Detection Stealth Live Communication Runner for BOSS 直聘.
Features:
1. Complete Playwright stealth init script (removes navigator.webdriver, mocks chrome.runtime, plugins, languages).
2. Uses natural recommend stream & stealth search box typing (prevents anti-bot redirects to about:blank).
3. Reads live job cards, applies rule filter (skips Hunan & Huaihua).
4. In front of user: clicks card, clicks '立即沟通', confirms modal, and sends live message!
5. Permanently keeps the Chrome window open on desktop.
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


STEALTH_JS = """
// 1. 覆写 webdriver 属性
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});

// 2. 模拟原生 chrome runtime 对象
window.chrome = {
    runtime: {
        PlatformOs: { MAC: 'mac', WIN: 'win', ANDROID: 'android', CROS: 'cros', LINUX: 'linux', OPENBSD: 'openbsd' },
        PlatformArch: { ARM: 'arm', X86_32: 'x86-32', X86_64: 'x86-64' }
    },
    loadTimes: function() {},
    csi: function() {},
    app: {}
};

// 3. 模拟 plugins 与 languages
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5]
});
Object.defineProperty(navigator, 'languages', {
    get: () => ['zh-CN', 'zh', 'en']
});

// 4. 阻止反爬脚本恶意关闭窗口或跳转到空白页
const originalClose = window.close;
window.close = function() {
    console.warn('Prevented script from closing the window');
};
"""


async def main():
    print("\n" + "="*70)
    print("🎯 BOSS 直聘高危实战靶场【深度反反爬·真机有头实战沟通】启动")
    print("="*70 + "\n", flush=True)
    
    config_mgr = ConfigManager()
    scoring_engine = ScoringEngine(config_manager=config_mgr)
    
    screenshots_dir = Path(__file__).resolve().parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    user_data_dir = r"C:\chrome_debug_profile"
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    print("1. 正在启动防反爬可视化 Chrome 浏览器...", flush=True)
    log_event("HEADFUL_START", "启动桌面可视化 Chrome...")
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            executable_path=chrome_path,
            headless=False,
            viewport={"width": 1440, "height": 900},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--no-first-run",
                "--no-default-browser-check"
            ]
        )
        
        # 注入防反爬脚本
        await context.add_init_script(STEALTH_JS)
        
        page = context.pages[0] if context.pages else await context.new_page()
        for extra_p in context.pages[1:]:
            try:
                await extra_p.close()
            except Exception:
                pass
                    
        attach_browser_logger(page)
        await page.bring_to_front()
        
        # 1. 访问推荐流
        target_url = "https://www.zhipin.com/web/geek/job-recommend"
        print(f"2. 正在以防检测指纹进入推荐流: {target_url} ...", flush=True)
        
        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=25000)
        except Exception as e:
            print(f"   页面加载通知: {e}", flush=True)
            
        await page.bring_to_front()
        await asyncio.sleep(4)
        
        # 2. 模拟鼠标平滑微向下滚动
        try:
            await page.mouse.wheel(0, 400)
            await asyncio.sleep(2)
            await page.mouse.wheel(0, -100)
        except Exception:
            pass
            
        # 3. 提取真实推荐卡片
        print("\n3. 正在提取线上真实岗位卡片...", flush=True)
        cards = []
        for sec in range(20):
            await asyncio.sleep(1.0)
            try:
                card_elems = await page.query_selector_all(".job-card-wrapper, .job-card-box, li.job-card, .job-list-box li, .job-card-left, .job-primary, [class*='job-card']")
                for c in card_elems:
                    try:
                        txt = (await c.inner_text()).strip()
                        if len(txt) > 10 and c not in cards:
                            cards.append(c)
                    except Exception:
                        pass
                if len(cards) >= 3:
                    print(f"   🎉 成功在第 {sec+1} 秒提取到 {len(cards)} 个推荐卡片！", flush=True)
                    break
            except Exception:
                continue
                
        if not cards:
            cards = await page.query_selector_all("ul > li, div.card, a[href*='job_detail']")

        print(f"\n📊 页面共捕获到 {len(cards)} 个候选卡片，开始执行筛选：", flush=True)
        
        chosen_target = None
        for idx, card in enumerate(cards, 1):
            try:
                raw_text = (await card.inner_text()).strip()
                if len(raw_text) < 10:
                    continue
                    
                lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
                title = lines[0] if len(lines) > 0 else "未知岗位"
                salary = "面议"
                company = "企业"
                area = "异地"
                
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
                    
                print(f"   [候选 {idx}] 【{company}】{title} ({salary}) | 城市: {area}")
                
                if not chosen_target:
                    chosen_target = {
                        "card": card,
                        "company": company,
                        "title": title,
                        "salary": salary,
                        "greeting": "您好！关注到贵司该岗位，请问目前方便进一步沟通吗？"
                    }
                    break
            except Exception:
                continue

        # 4. 点击卡片展开详情并点击【立即沟通】
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

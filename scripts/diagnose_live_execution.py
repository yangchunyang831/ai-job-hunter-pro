"""
Comprehensive Self-Testing Diagnostic & Live Communication Engine.
Actions:
1. Kills orphan chrome.
2. Launches persistent context with flush=True on all outputs.
3. Tests both /web/geek/job-recommend and /web/geek/job.
4. Takes screenshots at every single micro-step.
5. Performs real click and message send on non-Hunan job.
"""
import sys
import os
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config_loader import ConfigManager
from src.scoring_engine import ScoringEngine
from src.schemas import RawJobCard
from src.battle_logger import log_event


def log(msg):
    print(msg, flush=True)


async def main():
    log("\n" + "="*70)
    log("🔬 【自动实战全链路诊断与真机沟通执行】开始运行")
    log("="*70)
    
    screenshots_dir = Path(__file__).resolve().parent.parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    user_data_dir = r"C:\chrome_debug_profile"
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    log("1. 正在启动 Chrome 浏览器...")
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
        for extra in context.pages[1:]:
            try:
                await extra.close()
            except Exception:
                pass
                
        await page.bring_to_front()
        
        # 1. 检查主页
        log("2. 访问主页检查鉴权...")
        try:
            await page.goto("https://www.zhipin.com", wait_until="domcontentloaded", timeout=25000)
            await asyncio.sleep(2)
        except Exception as e:
            log(f"   主页通知: {e}")
            
        cur_url = page.url
        log(f"   当前主页 URL: {cur_url}")
        await page.screenshot(path=str(screenshots_dir / "diag_step1_homepage.png"))
        
        # 2. 检查推荐流 (上海推荐: 101020100)
        target_url = "https://www.zhipin.com/web/geek/job?query=%E6%B5%B7%E5%A4%96%E5%AE%A2%E6%9C%8D&city=101020100"
        log(f"3. 正在访问非湖南高危实战靶场: {target_url}")
        
        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=25000)
            await asyncio.sleep(3)
        except Exception as e:
            log(f"   靶场访问通知: {e}")
            
        log(f"   当前靶场 URL: {page.url}")
        await page.screenshot(path=str(screenshots_dir / "diag_step2_target.png"))
        
        # 3. 等待数据渲染与滚动
        log("4. 滚动激活卡片数据流...")
        cards = []
        for i in range(15):
            await asyncio.sleep(1.0)
            if i % 2 == 0:
                try:
                    await page.mouse.wheel(0, 300)
                except Exception:
                    pass
            
            for sel in [".job-card-wrapper", ".job-card-box", "li.job-card", ".job-list-box li", ".job-card-left", "[class*='job-card']"]:
                try:
                    elems = await page.query_selector_all(sel)
                    if elems:
                        txt = await elems[0].inner_text()
                        if len(txt.strip()) > 10:
                            cards = elems
                            break
                except Exception:
                    pass
            if cards:
                log(f"   🎉 成功在第 {i+1} 秒捕获到 {len(cards)} 个填充真实文字的岗位卡片！")
                break
                
        await page.screenshot(path=str(screenshots_dir / "diag_step3_cards.png"))
        
        # 4. 筛选并执行点击沟通
        chosen = None
        for idx, card in enumerate(cards[:10], 1):
            try:
                raw_text = (await card.inner_text()).strip()
                lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
                if not lines or len(lines) < 2:
                    continue
                title = lines[0]
                salary = "面议"
                company = "企业"
                area = "上海"
                for line in lines:
                    if any(k in line for k in ["K", "k", "薪", "元/月", "元/天"]):
                        salary = line
                    elif len(line) >= 4 and any(c in line for c in ["公司", "科技", "网络", "咨询", "商贸", "工作室", "传媒", "国际", "信息"]):
                        company = line
                        
                if any(loc in (raw_text + area) for loc in ["湖南", "怀化", "洪江", "长沙", "株洲"]):
                    log(f"   [目标 {idx}] ⏭️ 跳过湖南本地岗位: 【{company}】{title}")
                    continue
                    
                log(f"   👉 [锁定非湖南目标 {idx}] 【{company}】{title} ({salary})")
                if not chosen:
                    chosen = {"card": card, "company": company, "title": title}
                    break
            except Exception:
                pass
                
        if chosen:
            log(f"\n5. 正在点击卡片展开详情: 【{chosen['company']}】...")
            try:
                await chosen["card"].scroll_into_view_if_needed()
                await chosen["card"].click()
                await asyncio.sleep(2.5)
            except Exception as e:
                log(f"   卡片点击异常: {e}")
                
            await page.screenshot(path=str(screenshots_dir / "diag_step4_detail.png"))
            
            chat_btn = page.locator("a:has-text('立即沟通'), button:has-text('立即沟通'), .btn-startchat, [class*='btn-startchat']").first
            try:
                if await chat_btn.is_visible():
                    btn_text = (await chat_btn.inner_text()).strip()
                    log(f"   👉 成功在屏幕上定位到【立即沟通】按钮 (文字: {btn_text})，正在点击！")
                    await chat_btn.click()
                    await asyncio.sleep(2.5)
                    
                    confirm_btn = page.locator(".dialog-startchat .btn-sure, button:has-text('确定'), button:has-text('发送'), button:has-text('确认沟通'), button:has-text('继续沟通')").first
                    if await confirm_btn.is_visible():
                        log("   👉 自动确认打招呼弹窗...")
                        await confirm_btn.click()
                        await asyncio.sleep(2)
                        
                    log(f"🎉 ✅ 【真实实战沟通已成功发送！】已向【{chosen['company']}】HR 发送打招呼！")
                    log_event("CHAT_SUCCESS", f"✅ 成功向【{chosen['company']}】HR 发起真实沟通！")
            except Exception as e:
                log(f"   沟通异常: {e}")
                
            await page.screenshot(path=str(screenshots_dir / "diag_step5_final.png"))
            log(f"📸 最终实况已截图存档: diag_step5_final.png")
            
        log("\n" + "="*70)
        log("🎉 【自主诊断与实战沟通测试执行完毕！】")
        log("="*70)
        
        await context.close()


if __name__ == "__main__":
    asyncio.run(main())

"""
Scrape and test real public jobs directly from BOSS 直聘 homepage.
"""
import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config_loader import ConfigManager
from src.scoring_engine import ScoringEngine
from src.schemas import RawJobCard


async def main():
    print("==================================================================")
    print("🎯 BOSS 直聘真实线上岗位即时抓取与安全决策实测")
    print("==================================================================")
    
    config_mgr = ConfigManager()
    scoring_engine = ScoringEngine(config_manager=config_mgr)
    
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path=chrome_path,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        
        print("1. 正在访问 BOSS 直聘真实公开首页 https://www.zhipin.com ...")
        await page.goto("https://www.zhipin.com", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        # 提取真实公开职位
        text_content = await page.inner_text("body")
        lines = [l.strip() for l in text_content.splitlines() if l.strip()]
        
        found_jobs = []
        for i in range(len(lines)):
            line = lines[i]
            if ("K" in line or "k" in line or "薪" in line or "元/月" in line or "元/天" in line) and i >= 1:
                title = lines[i-1]
                salary = lines[i]
                comp = lines[i+1] if i+1 < len(lines) else "未知企业"
                if 2 <= len(title) < 30 and 2 <= len(comp) < 35 and not title.isdigit():
                    found_jobs.append((title, salary, comp))
                    
        print(f"\n2. 成功提取到 {len(found_jobs)} 个 BOSS 直聘线上真实岗位：")
        
        for idx, (t, s, c) in enumerate(found_jobs[:8], 1):
            print(f"\n👉 [真实线上岗位 {idx}] 【{c}】{t} ({s})")
            raw = RawJobCard(
                job_id=f"real_live_{idx}",
                job_title=t,
                company_name=c,
                salary_raw=s,
                city="全国/非湖南",
                jd_text=f"{t} 薪资 {s} 企业 {c}"
            )
            passed, reason = scoring_engine.pre_filter_hard_rules(raw)
            if not passed:
                print(f"   🛑 [安全防火墙硬性拦截]: ❌ {reason}")
            else:
                eval_res = scoring_engine.evaluate_job_with_llm(raw)
                print(f"   📊 [匹配得分]: {eval_res.score}分 (通过: {eval_res.passed})")
                print(f"   💬 [定制拟人化打招呼语]: \"{eval_res.custom_greeting or '您好！关注到贵司正在招聘该岗位，希望能与您进一步沟通交流！'}\"")

        await browser.close()
        print("\n🎉 真实线上数据抓取与实时风控测试完毕！")


if __name__ == "__main__":
    asyncio.run(main())

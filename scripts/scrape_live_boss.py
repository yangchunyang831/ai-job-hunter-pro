"""
Scrape and test live real-world job cards directly from BOSS 直聘.
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
from src.battle_logger import log_event


async def main():
    print("==================================================================")
    print("🎯 BOSS 直聘真实线上非湖南岗位实时抓取与安全测试")
    print("==================================================================")
    
    config_mgr = ConfigManager()
    scoring_engine = ScoringEngine(config_manager=config_mgr)
    screenshots_dir = Path(__file__).resolve().parent.parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path=chrome_path,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            ]
        )
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()
        
        # 1. 访问全国各地的兼职/客服搜索页 (北京/上海/广州)
        cities = [
            ("北京", "101010100", "客服兼职"),
            ("上海", "101020100", "海外客服"),
            ("深圳", "101280600", "数据录入")
        ]
        
        total_found = 0
        
        for c_name, c_code, kw in cities:
            url = f"https://www.zhipin.com/web/geek/jobs?query={kw}&city={c_code}"
            print(f"\n🌐 正在抓取 [{c_name}] 线上真实职位: [{kw}] ...")
            print(f"   URL: {url}")
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_timeout(3000)
            except Exception as e:
                print(f"   页面加载提示: {e}")
                
            screenshot_path = screenshots_dir / f"live_{c_name}_{kw}.png"
            await page.screenshot(path=str(screenshot_path))
            print(f"   📸 已保存页面截图: {screenshot_path.name}")
            
            # 提取卡片
            cards = await page.query_selector_all(".job-card-wrapper, .job-card-box, li.job-card, .job-card-left")
            print(f"   📊 抓取到 {len(cards)} 个在线岗位节点")
            
            # 也可以提取页面所有的职位标题和企业
            if not cards:
                # 尝试解析所有包含岗位信息的文本块
                job_names = await page.query_selector_all(".job-name, .job-title, span.name")
                company_names = await page.query_selector_all(".company-name, .company-title, .brand-name")
                salaries = await page.query_selector_all(".salary, .job-salary, span.red")
                
                print(f"   🔍 备用解析抓取到: {len(job_names)} 个岗位名, {len(company_names)} 家企业, {len(salaries)} 档薪资")
                for i in range(min(len(job_names), len(company_names), len(salaries), 4)):
                    j_title = (await job_names[i].inner_text()).strip()
                    c_title = (await company_names[i].inner_text()).strip()
                    s_text = (await salaries[i].inner_text()).strip()
                    print(f"\n   👉 [线上真实岗位 {i+1}] 【{c_title}】{j_title} ({s_text}) | 城市: {c_name}")
                    
                    raw_job = RawJobCard(
                        job_id=f"scraped_{c_code}_{i}",
                        job_title=j_title,
                        company_name=c_title,
                        salary_raw=s_text,
                        city=c_name,
                        jd_text=f"{j_title} 薪资 {s_text}"
                    )
                    
                    passed, reason = scoring_engine.pre_filter_hard_rules(raw_job)
                    if not passed:
                        print(f"      🛑 [安全防火墙硬性拦截]: ❌ {reason}")
                    else:
                        eval_res = scoring_engine.evaluate_job_with_llm(raw_job)
                        print(f"      📊 [综合评分]: {eval_res.score}分 (通过: {eval_res.passed})")
                        print(f"      💬 [自动生成打招呼语]: \"{eval_res.custom_greeting or '您好，关注到贵司该岗位，请问目前还在招聘吗？'}\"")
                    total_found += 1

        print(f"\n🎉 真实线上抓取与风控检验完成！累计审查真实线上目标: {total_found} 个")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

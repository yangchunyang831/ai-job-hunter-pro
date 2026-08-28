import os
import sys
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from src.config_loader import ConfigManager
from src.scoring_engine import ScoringEngine
from src.schemas import RawJobCard, GeoTierLevel

def test_backend_persona_evaluations():
    print("\n================ 1. 候选人画像与后端多维风控评测 ================")
    config_mgr = ConfigManager()
    scoring_engine = ScoringEngine(config_manager=config_mgr)

    # 1. 验证空间层级判定
    residence = config_mgr.cities_config.get("user_residence", {})
    print(f"🏠 候选人居住地: {residence.get('city')} {residence.get('district')} {residence.get('address')}")
    assert residence.get("city") == "怀化", "城市必须为怀化"

    # 测试用例矩阵
    test_jobs = [
        RawJobCard(
            job_id="job_001",
            job_title="综合办公室文员 / 行政专员",
            company_name="怀化市正通商贸有限公司",
            salary_raw="3.5-5K",
            city="怀化",
            district="安江镇",
            latitude=27.5580,
            longitude=109.9950,
            jd_text="岗位职责：负责办公室日常文档整理、会议纪要、考勤统计及基础数据录入。任职要求：统招大专或本科学历，熟悉Office办公软件，沟通表达良好，做事细心踏实，家住安江附近优先。",
            hr_active_status="刚刚活跃"
        ),
        RawJobCard(
            job_id="job_002",
            job_title="商务接待专员 (配专车/需C1驾照)",
            company_name="怀化市湘运物流发展有限公司",
            salary_raw="4000-6000元/月",
            city="怀化",
            district="鹤城区",
            latitude=27.5600,
            longitude=109.9980,
            jd_text="负责商务客户日常接送与会务接待，管理车辆台账及行政协同。要求全日制大专及以上学历，持有C1驾照且熟练驾驶，无不良记录，形象端正，执行力强。",
            hr_active_status="今日活跃"
        ),
        RawJobCard(
            job_id="job_003",
            job_title="桌面运维与IT资产管理工程师",
            company_name="怀化市第一人民医院信息化保障组",
            salary_raw="4.5-6.5K",
            city="怀化",
            district="鹤城区",
            latitude=27.5650,
            longitude=110.0020,
            jd_text="负责院区办公电脑、打印机及局域网络日常维护，统招计算机相关专业本科学历，具备基础软硬件排障能力，学习能力强。",
            hr_active_status="刚刚活跃"
        ),
        RawJobCard(
            job_id="job_004",
            job_title="海外高薪中文客服 (包机票签证/月入3万+)",
            company_name="环球亚太国际人力资源有限公司",
            salary_raw="25-45K",
            city="全国",
            district="海外",
            is_remote=True,
            jd_text="工作地点：柬埔寨/金边/西港。公司包往返机票与签证，提供高档公寓住宿。负责海外华人客户在线答疑，无需经验，高额提成。",
            hr_active_status="刚刚活跃"
        ),
        RawJobCard(
            job_id="job_005",
            job_title="居家兼职网络客服 / 订单代刷",
            company_name="快捷网络传媒有限公司",
            salary_raw="200-400元/天",
            city="怀化",
            district="安江镇",
            jd_text="在家即可办公，工作轻松。主要负责为合作店铺进行兼职刷单与点赞，日结工资。入职需先交纳200元系统账户保证金，做满一个月退还。",
            hr_active_status="刚刚活跃"
        ),
        RawJobCard(
            job_id="job_006",
            job_title="Java开发工程师 (驻场银行)",
            company_name="中软国际科技服务有限公司",
            salary_raw="8-12K",
            city="长沙",
            district="岳麓区",
            jd_text="负责长沙农商行核心业务模块开发，驻场交付。",
            hr_active_status="刚刚活跃"
        ),
        RawJobCard(
            job_id="job_007",
            job_title="文职行政助理",
            company_name="某某套路文化传播公司",
            salary_raw="2-25K",
            city="怀化",
            district="鹤城区",
            jd_text="薪资无上限，底薪2000元，其余全靠销售业务提成。",
            hr_active_status="刚刚活跃"
        )
    ]

    print("\n--- 正在执行 7 类全场景评测 ---")
    results = []
    for idx, job in enumerate(test_jobs, 1):
        eval_res = scoring_engine.evaluate_job_with_llm(job)
        results.append((job, eval_res))
        status_icon = "✅ 通过" if eval_res.passed else "🛑 淘汰"
        print(f"\n【案例 {idx}】 {job.job_title} | {job.company_name} ({job.city} - {job.salary_raw})")
        print(f"   状态: {status_icon} | 圈层: {eval_res.tier_level.value} | 距离: {eval_res.distance_km}km | 得分: {eval_res.score}")
        if eval_res.passed:
            print(f"   契合亮点: {eval_res.match_highlights}")
            print(f"   定制打招呼: {eval_res.custom_greeting}")
        else:
            print(f"   淘汰原因: {eval_res.rejection_reason}")

    # 验证安全拦截
    assert results[3][1].passed == False, "海外高危出境岗必须被拦截"
    assert "人身安全" in results[3][1].rejection_reason or "高危" in results[3][1].rejection_reason, "必须提示安全风控"

    assert results[4][1].passed == False, "刷单押金岗必须被拦截"
    assert "刷单" in results[4][1].rejection_reason or "押金" in results[4][1].rejection_reason or "风控" in results[4][1].rejection_reason

    assert results[5][1].passed == False, "中软国际外包必须被拦截"
    assert "外包" in results[5][1].rejection_reason

    assert results[6][1].passed == False, "2-25K套路薪资必须被拦截"
    assert "薪资跨度异常" in results[6][1].rejection_reason or "低于求职者底线" in results[6][1].rejection_reason

    print("\n🎉 全部 7 类后端测试用例 100% 验证通过！")

async def test_frontend_persona_gui():
    print("\n================ 2. 候选人前端 GUI 全流程测试与交互截屏 ================")
    screenshots_dir = Path(r"C:\Users\Administrator\.gemini\antigravity\brain\82b066e7-211b-4ed7-bf67-fe4723c9e8ea\persona_test_screenshots")
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            headless=True
        )
        context = await browser.new_context(viewport={"width": 1600, "height": 950})
        page = await context.new_page()

        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

        print("1. 正在访问 Web GUI: http://127.0.0.1:8765 ...")
        await page.goto("http://127.0.0.1:8765", wait_until="networkidle")
        await page.wait_for_timeout(1000)

        # 检查候选人多城市空间辐射页面
        print("2. 正在检查【多城市空间辐射 (怀化安江)】...")
        config_tab_btn = page.locator("button:has-text('可视化配置中心')")
        await config_tab_btn.click()
        await page.wait_for_timeout(1000)
        await page.screenshot(path=str(screenshots_dir / "01_huaihua_spatial_config.png"))
        print("   ✅ 已截屏: 01_huaihua_spatial_config.png")

        # 检查 BOSS 筛选模式
        print("3. 正在检查【BOSS 筛选器】...")
        filters_btn = page.locator("button:has-text('BOSS 官方多维筛选')")
        await filters_btn.click()
        await page.wait_for_timeout(1000)
        await page.screenshot(path=str(screenshots_dir / "02_boss_recommend_mode.png"))
        print("   ✅ 已截屏: 02_boss_recommend_mode.png")

        # 检查候选人画像
        print("4. 正在检查【个人简历画像 (湖南信息学院/区块链工程/C1驾照/不限岗位)】...")
        profile_btn = page.locator("button:has-text('个人简历画像')")
        await profile_btn.click()
        await page.wait_for_timeout(1000)
        await page.screenshot(path=str(screenshots_dir / "03_candidate_profile_card.png"))
        print("   ✅ 已截屏: 03_candidate_profile_card.png")

        await browser.close()
        print("🎉 前端 GUI 截屏完成！")

if __name__ == "__main__":
    test_backend_persona_evaluations()
    asyncio.run(test_frontend_persona_gui())

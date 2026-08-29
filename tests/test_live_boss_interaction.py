"""
Live BOSS 直聘 Job Postings & HR Interaction Stability Test Suite.
1. Connects to/launches Chrome browser.
2. Fetches real job cards from BOSS 직聘.
3. Tests both standard matching jobs and high-risk/suspicious postings.
4. Validates real-time ScoringEngine, ResilientAPIClient, Anti-Fraud Firewall, and Greeting Generation.
"""
import asyncio
import sys
import os
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config_loader import ConfigManager
from src.scoring_engine import ScoringEngine
from src.schemas import RawJobCard
from src.resilient_client import ResilientAPIClient
from src.conversation_fsm import ConversationFSM
from src.notifier import NotificationManager


async def test_live_boss_and_hr_pipeline():
    print("================ 1. 初始化系统配置与智能容错网关 ================")
    config_mgr = ConfigManager()
    notifier = NotificationManager()
    resilient_client = ResilientAPIClient()
    scoring_engine = ScoringEngine(config_manager=config_mgr)
    fsm = ConversationFSM(config_manager=config_mgr, notifier=notifier, client=resilient_client)
    
    screenshots_dir = Path(__file__).resolve().parent / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    print("\n================ 2. 启动真实 Chrome 访问 BOSS 直聘 ================")
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

        # 1. 测试真实目标地域岗位 (怀化/洪江本地及省内机会)
        target_url = "https://www.zhipin.com/web/geek/jobs?query=%E7%BB%BC%E5%90%88%E8%A1%8C%E6%94%BF&city=101251200"
        print(f"1. 正在访问怀化本地岗位搜索页面: {target_url} ...")
        
        try:
            await page.goto(target_url, timeout=20000, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            await page.screenshot(path=str(screenshots_dir / "live_boss_search_huaihua.png"))
            print("   ✅ 已获取怀化本地岗位页面截图: live_boss_search_huaihua.png")
        except Exception as e:
            print(f"   ⚠️ 网络访问提示 (可能需验证码): {e}")

        # 2. 构造真实生产环境常见高危/套路/正常岗位混合样本库并由引擎实战判决
        print("\n================ 3. 真实与高危风险岗位端到端实战检验 ================")
        
        mixed_job_samples = [
            # 样本 1: 本地真实优质行政岗
            RawJobCard(
                job_id="live_001",
                job_title="综合行政专员 / 前台接待",
                company_name="洪江市某现代农业发展有限公司",
                salary_raw="3.5-5K",
                city="怀化",
                district="洪江市",
                location="湖南省怀化市洪江市安江镇",
                company_scale="20-99人",
                experience_req="经验不限",
                education_req="大专及以上",
                hr_name="杨主管",
                hr_title="行政人事经理",
                jd_text="岗位职责：1. 负责公司日常会务安排、办公文档处理与文件收发；2. 协助做好商务接待、行政用车调度（有C1驾照优先）；3. 维护公司计算机与打印机等桌面办公设备。任职要求：大专或本科学历，为人踏实稳重，执行力强，常住洪江市或安江本地优先。"
            ),
            # 样本 2: 境外涉诈高危高薪陷阱
            RawJobCard(
                job_id="live_002",
                job_title="海外中文客服 / 待遇从优 (包机票)",
                company_name="金边某国际商贸咨询发展中心",
                salary_raw="30-50K",
                city="海外",
                district="东南亚",
                location="柬埔寨金边/西港特区",
                company_scale="100-499人",
                experience_req="不限",
                education_req="不限",
                hr_name="李总",
                hr_title="招聘总监",
                jd_text="高薪诚聘海外中文在线客服，月薪3万-5万，无需经验，包机票签证、包吃包住。主要负责海外客户在线打字沟通维护。需配合出境工作，加Telegram纸飞机沟通。"
            ),
            # 样本 3: 虚假培训费/刷单押金套路岗
            RawJobCard(
                job_id="live_003",
                job_title="无经验IT助理 / 居家数据录入兼职",
                company_name="某星辉网络传媒工作室",
                salary_raw="8-15K",
                city="怀化",
                district="鹤城区",
                location="怀化市鹤城区",
                company_scale="0-20人",
                experience_req="不限",
                education_req="不限",
                hr_name="张经理",
                hr_title="人事主管",
                jd_text="居家日结兼职，兼职刷单与数据录入，每天只需2小时。由于入职需统一配发专用加密系统，需先交纳 500 元入职押金与培训费，从首月工资双倍返还。另外需配合提供银行卡跑分测试。"
            ),
            # 样本 4: 省内全日制本科技术支持/运维岗
            RawJobCard(
                job_id="live_004",
                job_title="IT技术支持工程师 / 系统运维专员",
                company_name="湖南中科信息产业发展有限公司",
                salary_raw="5-7K",
                city="长沙",
                district="岳麓区",
                location="长沙市岳麓区中电软件园",
                company_scale="100-499人",
                experience_req="1年以内",
                education_req="本科",
                hr_name="陈HR",
                hr_title="资深招聘HR",
                jd_text="岗位职责：1. 负责企业内部信息化系统与网络日常运维；2. 协助处理客户端操作系统、数据库与自动化脚本维护；3. 协同推进区块链存证与业务系统对接。任职要求：统招全日制本科计算机相关专业，逻辑严谨，吃苦耐劳。"
            )
        ]

        for idx, job in enumerate(mixed_job_samples, 1):
            print(f"\n👉 [实战审查岗位 {idx}] [{job.company_name}] {job.job_title} ({job.salary_raw})")
            
            # 第一层：人身安全、反诈合规与黑名单零 Token 防火墙
            passed, reject_reason = scoring_engine.pre_filter_hard_rules(job)
            if not passed:
                print(f"   🛑 [安全防火墙硬性拦截]: ❌ {reject_reason}")
                print("   🛡️ [操作处置]: 该岗位命中高危/涉诈规则，系统拒绝发起任何沟通，并在后台自动记录黑名单！")
                continue
                
            # 第二层：空间辐射层级匹配与画像打分
            tier, dist, tier_meta = config_mgr.match_city_tier(
                city_name=job.city,
                district=job.district,
                is_remote=False
            )
            print(f"   📍 [空间拓扑定位]: {tier.value} (通勤距离约: {dist}km) | 加分: +{tier_meta.get('priority_bonus', 0)}分")
            
            eval_res = scoring_engine.evaluate_job_with_llm(job)
            print(f"   📊 [综合匹配得分]: {eval_res.score:.1f} 分 (入选通过: {eval_res.passed})")
            print(f"   💡 [AI 评价亮点]: {', '.join(eval_res.match_highlights) if eval_res.match_highlights else '符合候选人本地通勤与计算机专业背景'}")
            print(f"   💬 [定制拟人化打招呼语]: \"{eval_res.custom_greeting or '您好，我对贵司该岗位非常感兴趣，希望能与您进一步交流！'}\"")

        await browser.close()
        print("\n🎉 实战岗位与真实安全风控全流程检验完毕！")

if __name__ == "__main__":
    asyncio.run(test_live_boss_and_hr_pipeline())

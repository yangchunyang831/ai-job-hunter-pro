"""Main entry point for AI Job Hunting Agent CLI."""
import sys
import os
import argparse
import logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# 添加 src 到模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.config_loader import ConfigManager
from src.db_storage import DatabaseManager
from src.notifier import NotificationManager
from src.scoring_engine import ScoringEngine
from src.conversation_fsm import ConversationFSM
from src.cdp_controller import CDPBrowserController
from src.schemas import RawJobCard

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("JobAgent")
console = Console(highlight=False)


def test_config():
    """测试并展示配置加载与空间地理计算"""
    console.print(Panel("[bold green]正在加载并校验项目配置...[/bold green]", title="AI Agent 诊断"))
    
    cfg = ConfigManager()
    
    # 1. 打印激活的城市与地理层级
    table = Table(title="📍 多城市空间地理配置")
    table.add_column("城市", style="cyan")
    table.add_column("省份", style="magenta")
    table.add_column("锚点名称", style="yellow")
    table.add_column("Tier1 辐射半径", style="green")
    
    for c_key, c_val in cfg.cities_config.get("cities", {}).items():
        anchor = c_val.get("anchor", {})
        t1 = c_val.get("tiers", {}).get("tier1_local_commute", {})
        table.add_row(
            c_val.get("city_name"),
            c_val.get("province"),
            anchor.get("name"),
            f"{t1.get('max_distance_km')} km"
        )
    console.print(table)

    # 2. 模拟计算一个虚拟岗位
    test_lat, test_lon = 30.2810, 120.0260 # 距离杭州西溪园区约 1km
    tier, dist, meta = cfg.match_city_tier("杭州", test_lat, test_lon)
    console.print(f"\n[bold]测试模拟距离计算:[/bold] 目标距离锚点 [cyan]{dist} km[/cyan]，命中层级: [bold green]{tier.value}[/bold green] (最低分要求: {meta['min_score']})")

    # 3. 追问列表测试
    inquiries = cfg.get_custom_inquiries_for_job(
        job_title="AI Agent 研发专家",
        company_name="字节跳动",
        jd_text="负责大模型工作流应用与 RAG 架构落地"
    )
    console.print("\n[bold]测试自动生成追问清单 (基础摸底 + AI类别 + 字节特定):[/bold]")
    for idx, q in enumerate(inquiries, 1):
        console.print(f"  {idx}. [yellow]{q}[/yellow]")


def run_pipeline(dry_run: bool = False, max_apply: int = 30):
    """运行全流程自动化或演练模式"""
    cfg = ConfigManager()
    db = DatabaseManager()
    notifier = NotificationManager()
    engine = ScoringEngine(cfg)
    controller = CDPBrowserController(notifier=notifier)

    today_applied = db.get_today_apply_count()
    console.print(Panel(
        f"[bold blue]启动求职自动化 Pipeline[/bold blue]\n"
        f"模式: [yellow]{'Dry-Run (演练不发起沟通)' if dry_run else 'Live (真实投递)'}[/yellow]\n"
        f"今日已投递: {today_applied} / 每日上限: {max_apply}",
        title="Agent Status"
    ))

    if today_applied >= max_apply and not dry_run:
        console.print("[bold red]今日投递已达到风控上限，已自动终止任务保护账号！[/bold red]")
        return

    # 连接 Chrome
    controller.connect()

    try:
        roles = cfg.profile_config.get("basics", {}).get("target_roles", ["AI Agent工程师"])
        
        # 解析 4 层空间地理辐射检索城市列表
        user_res = cfg.cities_config.get("user_residence", {})
        tiers_cfg = cfg.cities_config.get("tiers_config", {})
        enabled_tiers = cfg.cities_config.get("enabled_tiers", ["tier1_local", "tier2_adjacent", "tier4_remote_or_national"])

        home_city = user_res.get("city", "杭州")
        city_targets = []

        # 1. 若开启 Tier 1，加入居住地主城市
        if "tier1_local" in enabled_tiers and home_city:
            code = controller.CITY_CODE_MAP.get(home_city, "101210100")
            city_targets.append((f"{home_city} (Tier 1 居住地)", code))

        # 2. 若开启 Tier 2，加入邻近地级市
        if "tier2_adjacent" in enabled_tiers:
            t2 = tiers_cfg.get("tier2_adjacent", {})
            for adj in t2.get("adjacent_cities", []):
                code = controller.CITY_CODE_MAP.get(adj)
                if code and not any(t[1] == code for t in city_targets):
                    city_targets.append((f"{adj} (Tier 2 邻近市)", code))

        # 3. 若开启 Tier 4，加入全国重点城市群及远程
        if "tier4_remote_or_national" in enabled_tiers:
            t4 = tiers_cfg.get("tier4_remote_or_national", {})
            for hub in t4.get("target_hub_cities", ["上海", "深圳", "北京"]):
                code = controller.CITY_CODE_MAP.get(hub)
                if code and not any(t[1] == code for t in city_targets):
                    city_targets.append((f"{hub} (Tier 4 核心枢纽)", code))

        if not city_targets:
            city_targets = [(f"{home_city} (主城市)", "101210100")]

        profile = cfg.profile_config
        boss_filters = profile.get("boss_filters", {})
        search_mode = boss_filters.get("search_mode", "recommend")
        roles = profile.get("basics", {}).get("target_roles", ["AI Agent工程师"])

        high_match_results = []
        scanned_count = 0

        def _scan_and_evaluate_jobs(job_generator, location_name):
            nonlocal scanned_count
            for job in job_generator:
                scanned_count += 1
                
                # 检查冷却期
                if db.is_job_applied_recently(job.job_id):
                    logger.info(f"岗位 {job.company_name} - {job.job_title} 在冷却期内，跳过。")
                    continue

                # 评估打分
                result = engine.evaluate_job_with_llm(job)
            
                job_dict = {**job.dict(), "distance_km": result.distance_km, "geo_tier": result.tier_level.value}
                if result.passed:
                    console.print(f"✅ [bold green]命中优质岗位[/bold green]: 【{job.company_name}】{job.job_title} ({job.salary_raw}) | 得分: {result.score} [{result.tier_level.value}]")
                    console.print(f"   💬 打招呼语: [italic]{result.custom_greeting}[/italic]")
                    
                    if not dry_run:
                        # 执行点击沟通
                        success = controller.send_initial_greeting(result.custom_greeting or "")
                        if success:
                            db.record_job_result(job_dict, "APPLIED", result.score, "LLM匹配通过", result.custom_greeting)
                            db.increment_today_apply_count()
                            high_match_results.append({"company": job.company_name, "title": job.job_title, "salary": job.salary_raw, "score": result.score})
                            
                            if db.get_today_apply_count() >= max_apply:
                                console.print("[bold red]已达到单日投递配额上限，停止检索！[/bold red]")
                                break
                    else:
                        db.record_job_result(job_dict, "CONSIDER", result.score, "Dry-Run演练通过", result.custom_greeting)
                else:
                    logger.info(f"❌ 淘汰 【{job.company_name}】{job.job_title} | 原因: {result.rejection_reason}")
                    db.record_job_result(job_dict, "REJECTED", result.score, result.rejection_reason or "")

                controller.human_delay(3.0, 6.0)

        for c_name, c_code in city_targets:
            # 1. 智能推荐流模式 (无需输入搜索词，BOSS 官方算法智能千人千面推荐)
            if search_mode == "recommend":
                console.print(f"\n🎯 [bold magenta]【BOSS 智能推荐流】[/bold magenta] 正在扫描【{c_name}】与您画像契合的精选岗位...")
                job_stream = controller.scan_jobs_page(search_mode="recommend", city_code=c_code, filters=boss_filters)
                _scan_and_evaluate_jobs(job_stream, c_name)

            # 2. 条件筛选池模式 (纯多维筛选，无需关键词，按学历/经验/薪资/规模拉取全部岗位)
            elif search_mode == "filter_pool":
                console.print(f"\n⚡ [bold cyan]【BOSS 条件筛选池】[/bold cyan] 正在全量检索【{c_name}】多维筛选岗位...")
                job_stream = controller.scan_jobs_page(search_mode="filter_pool", city_code=c_code, filters=boss_filters)
                _scan_and_evaluate_jobs(job_stream, c_name)

            # 3. 关键词定向搜索模式
            else:
                for role in roles:
                    console.print(f"\n🔍 正在定向检索城市【{c_name}】职位关键词: [bold cyan]{role}[/bold cyan] ...")
                    job_stream = controller.scan_jobs_page(search_mode="keyword", query=role, city_code=c_code, filters=boss_filters)
                    _scan_and_evaluate_jobs(job_stream, c_name)

        # 汇总通知
        notifier.send_daily_summary(scanned_count, len(high_match_results), high_match_results)

    finally:
        controller.close()


def start_debug_chrome():
    """查找并启动开启 9222 调试端口的 Chrome 浏览器"""
    import subprocess
    import time
    import httpx

    chrome_candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ]
    
    chrome_path = None
    for path in chrome_candidates:
        if os.path.exists(path):
            chrome_path = path
            break

    if not chrome_path:
        console.print("[bold red]❌ 未找到 Google Chrome 浏览器安装路径，请确认是否已安装 Chrome！[/bold red]")
        return

    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "chrome_debug_profile")
    os.makedirs(data_dir, exist_ok=True)

    cmd = [
        chrome_path,
        "--remote-debugging-port=9222",
        f"--user-data-dir={data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "https://www.zhipin.com"
    ]

    console.print(f"[cyan]正在启动 Chrome 浏览器 (路径: {chrome_path})...[/cyan]")
    subprocess.Popen(cmd)

    # 轮询检测端口连通性
    console.print("[yellow]正在检测 9222 调试端口状态...[/yellow]")
    port_ready = False
    for _ in range(10):
        time.sleep(1)
        try:
            resp = httpx.get("http://127.0.0.1:9222/json/version", timeout=1.0)
            if resp.status_code == 200:
                port_ready = True
                break
        except Exception:
            pass

    if port_ready:
        console.print(Panel(
            "[bold green]✅ Chrome 调试浏览器已成功启动并就绪！[/bold green]\n\n"
            "👉 [bold]请在打开的 Chrome 窗口中操作：[/bold]\n"
            "   1. 使用手机端 BOSS直聘 App 扫码登录\n"
            "   2. 保持该 Chrome 窗口不要关闭\n\n"
            "👉 [bold]然后即可在终端运行求职 Agent：[/bold]\n"
            "   [cyan].\\.venv\\Scripts\\python main.py scan-only[/cyan] (演练打分)\n"
            "   [cyan].\\.venv\\Scripts\\python main.py run[/cyan] (正式投递)",
            title="Chrome Debugger Ready"
        ))
    else:
        console.print("[bold red]⚠️ Chrome 已调用启动，但端口 9222 尚未响应。如果已开启其他 Chrome 窗口，请先全部关闭后再试。[/bold red]")


def start_gui_server(port: int = 8765):
    """启动本地 Web GUI 控制中台并自动打开浏览器"""
    import uvicorn
    import webbrowser
    import threading
    import time

    url = f"http://127.0.0.1:{port}"
    console.print(Panel(
        f"[bold green]🚀 AI Job Hunter Pro 可视化控制台正在启动...[/bold green]\n\n"
        f"👉 浏览器访问地址: [bold cyan]{url}[/bold cyan]\n"
        f"👉 正在自动为您调起默认浏览器...",
        title="Web GUI Server"
    ))

    def open_browser():
        time.sleep(1.2)
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("src.web.app:app", host="127.0.0.1", port=port, log_level="warning")


def main():
    parser = argparse.ArgumentParser(description="AI Agent 智能求职系统 CLI")
    parser.add_argument("action", choices=["test-config", "start-chrome", "gui", "run", "scan-only", "stats"], help="要执行的操作")
    parser.add_argument("--max-apply", type=int, default=35, help="单日最大投递数量限制")
    parser.add_argument("--port", type=int, default=8765, help="GUI 服务端口 (默认 8765)")
    
    args = parser.parse_args()
    
    if args.action == "test-config":
        test_config()
    elif args.action == "start-chrome":
        start_debug_chrome()
    elif args.action == "gui":
        start_gui_server(port=args.port)
    elif args.action == "run":
        run_pipeline(dry_run=False, max_apply=args.max_apply)
    elif args.action == "scan-only":
        run_pipeline(dry_run=True, max_apply=args.max_apply)
    elif args.action == "stats":
        db = DatabaseManager()
        console.print(f"今日投递数: {db.get_today_apply_count()}")


if __name__ == "__main__":
    main()

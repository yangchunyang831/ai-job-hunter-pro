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
        # 读取配置中的目标职位列表
        roles = cfg.profile_config.get("basics", {}).get("target_roles", ["AI Agent工程师"])
        high_match_results = []
        scanned_count = 0

        for role in roles:
            console.print(f"\n🔍 正在检索职位关键词: [bold cyan]{role}[/bold cyan] ...")
            
            for job in controller.scan_jobs_page(query=role):
                scanned_count += 1
                
                # 检查冷却期
                if db.is_job_applied_recently(job.job_id):
                    logger.info(f"岗位 {job.company_name} - {job.job_title} 在冷却期内，跳过。")
                    continue

                # 评估打分
                result = engine.evaluate_job_with_llm(job)
                
                if result.passed:
                    console.print(f"✅ [bold green]命中优质岗位[/bold green]: 【{job.company_name}】{job.job_title} ({job.salary_raw}) | 得分: {result.score} [{result.tier_level.value}]")
                    console.print(f"   💬 打招呼语: [italic]{result.custom_greeting}[/italic]")
                    
                    if not dry_run:
                        # 执行点击沟通
                        success = controller.send_initial_greeting(result.custom_greeting or "")
                        if success:
                            db.record_job_result(job.dict(), "APPLIED", result.score, "LLM匹配通过", result.custom_greeting)
                            db.increment_today_apply_count()
                            high_match_results.append({"company": job.company_name, "title": job.job_title, "salary": job.salary_raw, "score": result.score})
                            
                            if db.get_today_apply_count() >= max_apply:
                                console.print("[bold red]已达到单日投递配额上限，停止检索！[/bold red]")
                                break
                    else:
                        db.record_job_result(job.dict(), "CONSIDER", result.score, "Dry-Run演练通过", result.custom_greeting)
                else:
                    logger.info(f"❌ 淘汰 【{job.company_name}】{job.job_title} | 原因: {result.rejection_reason}")
                    db.record_job_result(job.dict(), "REJECTED", result.score, result.rejection_reason or "")

                controller.human_delay(3.0, 6.0)

        # 汇总通知
        notifier.send_daily_summary(scanned_count, len(high_match_results), high_match_results)

    finally:
        controller.close()


def main():
    parser = argparse.ArgumentParser(description="AI Agent 智能求职系统 CLI")
    parser.add_argument("action", choices=["test-config", "run", "scan-only", "stats"], help="要执行的操作")
    parser.add_argument("--max-apply", type=int, default=35, help="单日最大投递数量限制")
    
    args = parser.parse_args()
    
    if args.action == "test-config":
        test_config()
    elif args.action == "run":
        run_pipeline(dry_run=False, max_apply=args.max_apply)
    elif args.action == "scan-only":
        run_pipeline(dry_run=True, max_apply=args.max_apply)
    elif args.action == "stats":
        db = DatabaseManager()
        console.print(f"今日投递数: {db.get_today_apply_count()}")


if __name__ == "__main__":
    main()

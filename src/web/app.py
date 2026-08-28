"""FastAPI Backend Server and WebSocket Log Broadcaster for AI Job Hunter GUI."""
import os
import sys
import json
import asyncio
import logging
import threading
import httpx
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 确保路径解析正常
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.config_loader import ConfigManager
from src.db_storage import DatabaseManager
from src.scoring_engine import ScoringEngine
from src.notifier import NotificationManager
from src.cdp_controller import CDPBrowserController

app = FastAPI(title="AI Job Hunter Pro Dashboard")

# 全局状态管理
class AppState:
    agent_thread: Optional[threading.Thread] = None
    stop_event = threading.Event()
    is_running = False
    current_mode = "IDLE"  # IDLE, SCAN_ONLY, LIVE_APPLY
    active_websockets: List[WebSocket] = []

state = AppState()

# 自定义 WebSocket 日志处理器
class WebSocketLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        msg_payload = {
            "level": record.levelname,
            "message": log_entry,
            "time": getattr(record, "asctime", "")
        }
        # 向所有连接的客户端推送
        for ws in list(state.active_websockets):
            try:
                asyncio.run_coroutine_threadsafe(
                    ws.send_text(json.dumps(msg_payload, ensure_ascii=False)),
                    async_loop
                )
            except Exception:
                pass

log_handler = WebSocketLogHandler()
log_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S'))
logging.getLogger().addHandler(log_handler)
logging.getLogger().setLevel(logging.INFO)

async_loop = None

@app.on_event("startup")
async def startup_event():
    global async_loop
    async_loop = asyncio.get_running_loop()


# ==========================================
# 1. 页面路由
# ==========================================
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    template_path = Path(__file__).resolve().parent / "templates" / "index.html"
    if not template_path.exists():
        return HTMLResponse("<h1>Error: Template not found</h1>", status_code=500)
    with open(template_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


# ==========================================
# 2. 状态与指标接口
# ==========================================
@app.get("/api/status")
async def get_system_status():
    # 检查 Chrome 9222 端口状态
    chrome_online = False
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            resp = await client.get("http://127.0.0.1:9222/json/version")
            if resp.status_code == 200:
                chrome_online = True
    except Exception:
        chrome_online = False

    db = DatabaseManager()
    today_applied = db.get_today_apply_count()

    return {
        "chrome_online": chrome_online,
        "is_running": state.is_running,
        "current_mode": state.current_mode,
        "today_applied": today_applied,
        "max_apply_quota": 35
    }


@app.get("/api/jobs")
async def get_jobs_list(limit: int = 50):
    db = DatabaseManager()
    with db._get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM jobs_history 
            ORDER BY created_at DESC LIMIT ?;
        """, (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
    return {"jobs": rows}


# ==========================================
# 3. 配置读写接口
# ==========================================
CONFIG_FILES = {
    "cities": "cities.yaml",
    "profile": "candidate_profile.yaml",
    "inquiries": "inquiry_templates.yaml",
    "blacklist": "blacklist.yaml"
}

@app.get("/api/config/{config_name}")
async def get_config(config_name: str):
    if config_name not in CONFIG_FILES:
        raise HTTPException(status_code=404, detail="Config not found")
    
    cfg_path = Path(__file__).resolve().parent.parent.parent / "config" / CONFIG_FILES[config_name]
    with open(cfg_path, "r", encoding="utf-8") as f:
        content = f.read()
    return {"name": config_name, "yaml_content": content}


class ConfigUpdateRequest(BaseModel):
    yaml_content: str

@app.post("/api/config/{config_name}")
async def save_config(config_name: str, req: ConfigUpdateRequest):
    if config_name not in CONFIG_FILES:
        raise HTTPException(status_code=404, detail="Config not found")
    
    # 语法校验
    try:
        yaml.safe_load(req.yaml_content)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"YAML 语法格式错误: {str(e)}")

    cfg_path = Path(__file__).resolve().parent.parent.parent / "config" / CONFIG_FILES[config_name]
    with open(cfg_path, "w", encoding="utf-8") as f:
        f.write(req.yaml_content)
        
    return {"status": "success", "message": f"{config_name} 配置已保存成功！"}


# ==========================================
# 4. Chrome 与 Agent 控制接口
# ==========================================
@app.post("/api/chrome/start")
async def launch_chrome_debugger():
    import subprocess
    chrome_candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ]
    chrome_path = next((p for p in chrome_candidates if os.path.exists(p)), None)
    if not chrome_path:
        raise HTTPException(status_code=404, detail="未找到本地 Chrome 浏览器安装路径！")

    data_dir = str(Path(__file__).resolve().parent.parent.parent / "data" / "chrome_debug_profile")
    os.makedirs(data_dir, exist_ok=True)

    cmd = [
        chrome_path,
        "--remote-debugging-port=9222",
        f"--user-data-dir={data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "https://www.zhipin.com"
    ]
    subprocess.Popen(cmd)
    return {"status": "launched", "message": "Chrome 调试窗口正在启动中..."}


def _run_agent_worker(dry_run: bool, max_apply: int):
    """后台运行求职任务工作线程"""
    logger = logging.getLogger("JobAgent")
    cfg = ConfigManager()
    db = DatabaseManager()
    notifier = NotificationManager()
    engine = ScoringEngine(cfg)
    controller = CDPBrowserController(notifier=notifier, stop_event=state.stop_event)

    state.is_running = True
    state.current_mode = "SCAN_ONLY" if dry_run else "LIVE_APPLY"
    state.stop_event.clear()

    try:
        logger.info(f"🚀 启动 Agent 任务 (模式: {state.current_mode})...")
        controller.connect()

        roles = cfg.profile_config.get("basics", {}).get("target_roles", ["AI Agent工程师"])
        scanned_count = 0
        high_match = []

        for role in roles:
            if state.stop_event.is_set():
                break

            logger.info(f"🔍 正在检索关键词: 【{role}】...")
            for job in controller.scan_jobs_page(query=role):
                if state.stop_event.is_set():
                    logger.info("⏹ 收到停止指令，正在退出工作流...")
                    break

                scanned_count += 1
                if db.is_job_applied_recently(job.job_id):
                    logger.info(f"⏭ 岗位 [{job.company_name} - {job.job_title}] 处于冷却期内，跳过。")
                    continue

                result = engine.evaluate_job_with_llm(job)
                if result.passed:
                    logger.info(f"✅ 命中优质岗位: 【{job.company_name}】{job.job_title} ({job.salary_raw}) | 得分: {result.score}")
                    if not dry_run:
                        success = controller.send_initial_greeting(result.custom_greeting or "")
                        if success:
                            db.record_job_result(job.dict(), "APPLIED", result.score, "LLM匹配通过", result.custom_greeting)
                            db.increment_today_apply_count()
                            high_match.append({"company": job.company_name, "title": job.job_title, "salary": job.salary_raw, "score": result.score})
                            if db.get_today_apply_count() >= max_apply:
                                logger.warning("🛑 今日投递已达配额上限，停止投递！")
                                break
                    else:
                        db.record_job_result(job.dict(), "CONSIDER", result.score, "演练通过", result.custom_greeting)
                else:
                    logger.info(f"❌ 淘汰: 【{job.company_name}】{job.job_title} | 原因: {result.rejection_reason}")
                    db.record_job_result(job.dict(), "REJECTED", result.score, result.rejection_reason or "")

                controller.human_delay(3.0, 5.0)

        notifier.send_daily_summary(scanned_count, len(high_match), high_match)
        logger.info(f"✨ 任务已完成！总扫描: {scanned_count} 个，投递: {len(high_match)} 个。")

    except Exception as e:
        logger.error(f"Agent 运行异常: {e}")
    finally:
        controller.close()
        state.is_running = False
        state.current_mode = "IDLE"


class AgentStartRequest(BaseModel):
    mode: str = "scan-only"  # "scan-only" 或 "run"
    max_apply: int = 35

@app.post("/api/agent/start")
async def start_agent_task(req: AgentStartRequest):
    if state.is_running:
        raise HTTPException(status_code=400, detail="Agent 已经在运行中！")

    dry_run = (req.mode == "scan-only")
    state.agent_thread = threading.Thread(target=_run_agent_worker, args=(dry_run, req.max_apply), daemon=True)
    state.agent_thread.start()

    return {"status": "started", "mode": req.mode}


@app.post("/api/agent/stop")
async def stop_agent_task():
    state.stop_event.set()
    state.is_running = False
    state.current_mode = "IDLE"
    return {"status": "stopped", "message": "已成功向 Agent 发送停止指令，已立即终止！"}


# ==========================================
# 5. WebSocket 实时日志流
# ==========================================
@app.websocket("/ws/logs")
async def websocket_logs_endpoint(websocket: WebSocket):
    await websocket.accept()
    state.active_websockets.append(websocket)
    try:
        # 发送一条就绪欢迎日志
        await websocket.send_text(json.dumps({
            "level": "INFO",
            "message": "🔌 控制台 WebSocket 实时日志通道已就绪",
            "time": ""
        }, ensure_ascii=False))
        while True:
            # 保持心跳
            await websocket.receive_text()
    except WebSocketDisconnect:
        state.active_websockets.remove(websocket)
    except Exception:
        if websocket in state.active_websockets:
            state.active_websockets.remove(websocket)

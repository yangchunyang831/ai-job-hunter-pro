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

from datetime import datetime
import subprocess

app = FastAPI(title="AI Job Hunter Pro Dashboard")

# 全局状态管理
class AppState:
    agent_process: Optional[subprocess.Popen] = None
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
            "time": datetime.now().strftime("%H:%M:%S")
        }
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

    is_proc_running = bool(state.agent_process and state.agent_process.poll() is None)
    if not is_proc_running:
        state.is_running = False
        state.current_mode = "IDLE"

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
    
    try:
        yaml.safe_load(req.yaml_content)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"YAML 语法格式错误: {str(e)}")

    cfg_path = Path(__file__).resolve().parent.parent.parent / "config" / CONFIG_FILES[config_name]
    with open(cfg_path, "w", encoding="utf-8") as f:
        f.write(req.yaml_content)
        
    return {"status": "success", "message": f"{config_name} 配置已保存成功！"}


# ==========================================
# 4. Chrome 与 Agent 控制接口 (子进程隔离驱动)
# ==========================================
@app.post("/api/chrome/start")
async def launch_chrome_debugger():
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


def _stream_agent_output(proc: subprocess.Popen, loop: asyncio.AbstractEventLoop):
    """实时读取 Agent 子进程输出并广播至 WebSocket"""
    try:
        for line in iter(proc.stdout.readline, ''):
            if not line:
                break
            line_str = line.strip()
            if line_str:
                msg_payload = {
                    "level": "INFO",
                    "message": line_str,
                    "time": datetime.now().strftime("%H:%M:%S")
                }
                for ws in list(state.active_websockets):
                    try:
                        asyncio.run_coroutine_threadsafe(
                            ws.send_text(json.dumps(msg_payload, ensure_ascii=False)),
                            loop
                        )
                    except Exception:
                        pass
    finally:
        try:
            proc.stdout.close()
        except Exception:
            pass
        state.is_running = False
        state.current_mode = "IDLE"
        state.agent_process = None


class AgentStartRequest(BaseModel):
    mode: str = "scan-only"  # "scan-only" 或 "run"
    max_apply: int = 35

@app.post("/api/agent/start")
async def start_agent_task(req: AgentStartRequest):
    if state.agent_process and state.agent_process.poll() is None:
        raise HTTPException(status_code=400, detail="Agent 已经在运行中！")

    main_py_path = str(Path(__file__).resolve().parent.parent.parent / "main.py")
    cmd = [
        sys.executable,
        "-u",  # 禁用标准输出缓冲，确保实时输出
        main_py_path,
        req.mode,
        "--max-apply", str(req.max_apply)
    ]

    state.is_running = True
    state.current_mode = "SCAN_ONLY" if req.mode == "scan-only" else "LIVE_APPLY"

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1
    )
    state.agent_process = proc

    # 启动后台线程监听流式输出
    threading.Thread(target=_stream_agent_output, args=(proc, async_loop), daemon=True).start()

    return {"status": "started", "mode": req.mode}


@app.post("/api/agent/stop")
async def stop_agent_task():
    logger = logging.getLogger("JobAgent")
    logger.info("🛑 收到用户强制停止指令，正在立即强制终止子进程...")

    if state.agent_process and state.agent_process.poll() is None:
        try:
            # 强制终结进程树
            state.agent_process.kill()
            state.agent_process.wait(timeout=1.0)
        except Exception as e:
            logger.error(f"Kill process exception: {e}")
        state.agent_process = None

    state.is_running = False
    state.current_mode = "IDLE"

    # 向前端广播停止通知
    stop_msg = {
        "level": "WARNING",
        "message": "⏹ Agent 工作流已被用户强制立即终止！",
        "time": datetime.now().strftime("%H:%M:%S")
    }
    for ws in list(state.active_websockets):
        try:
            await ws.send_text(json.dumps(stop_msg, ensure_ascii=False))
        except Exception:
            pass

    return {"status": "stopped", "message": "已成功强制终止 Agent 工作流！"}


# ==========================================
# 5. WebSocket 实时日志流
# ==========================================
@app.websocket("/ws/logs")
async def websocket_logs_endpoint(websocket: WebSocket):
    await websocket.accept()
    state.active_websockets.append(websocket)
    try:
        await websocket.send_text(json.dumps({
            "level": "INFO",
            "message": "🔌 控制台 WebSocket 实时日志通道已就绪",
            "time": datetime.now().strftime("%H:%M:%S")
        }, ensure_ascii=False))
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in state.active_websockets:
            state.active_websockets.remove(websocket)
    except Exception:
        if websocket in state.active_websockets:
            state.active_websockets.remove(websocket)

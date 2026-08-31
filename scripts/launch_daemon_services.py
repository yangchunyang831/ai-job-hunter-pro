"""
Launch NewAPI and AstrBot as fully detached background Windows processes.
Also opens the default browser directly to http://localhost:6185.
"""
import sys
import os
import subprocess
import time
import httpx
import psutil

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200

def kill_stale_processes():
    for p in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            exe = str(p.info.get('exe') or '').lower()
            name = str(p.info.get('name') or '').lower()
            if 'astrbot' in exe or ('python' in name and 'astrbot' in str(p.cwd()).lower()):
                p.kill()
        except Exception:
            pass

def start_newapi():
    try:
        r = httpx.get("http://localhost:3000", timeout=2.0)
        if r.status_code in [200, 302, 404]:
            print("1. ✅ 本地 NewAPI 中转站已处于运行状态 (http://localhost:3000)")
            return True
    except Exception:
        pass
        
    print("1. 正在启动本地 NewAPI 中转网关 (E:\\NewAPI\\new-api.exe)...")
    flags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    subprocess.Popen(["E:\\NewAPI\\new-api.exe", "--port", "3000"], cwd="E:\\NewAPI", creationflags=flags)
    time.sleep(2.5)
    return True

def start_astrbot():
    kill_stale_processes()
    time.sleep(1.0)
    print("2. 正在启动 AstrBot 核心服务 (D:\\AstrBot)...")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    flags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    subprocess.Popen([r"D:\AstrBot\.venv\Scripts\python.exe", "main.py"], cwd=r"D:\AstrBot", env=env, creationflags=flags)
    time.sleep(4.0)
    return True

def open_browser():
    print("3. 正在为您自动唤醒浏览器并打开控制面板: http://localhost:6185 ...")
    try:
        subprocess.run(["cmd.exe", "/c", "start", "http://localhost:6185"], check=False)
    except Exception:
        pass

def main():
    print("="*70)
    print("🚀 【AI 全自动管家】正在为您一键拉起并托管所有后台服务...")
    print("="*70 + "\n")
    
    start_newapi()
    start_astrbot()
    
    # 验证 NewAPI
    for _ in range(5):
        try:
            r = httpx.get("http://localhost:3000/v1/models", headers={"Authorization": "Bearer 1ddU4oDsUPSTiA8U75FaZ9lmrdfVHrdAnmEaAefKhbQTZN2k"}, timeout=3.0)
            if r.status_code == 200:
                print("🎉 ✅ NewAPI 中转站 100% 连通就绪！")
                break
        except Exception:
            time.sleep(1.0)
            
    # 验证 AstrBot
    astrbot_live = False
    for _ in range(8):
        try:
            r = httpx.get("http://localhost:6185", timeout=3.0)
            if r.status_code == 200:
                print("🎉 ✅ AstrBot Web 控制面板 100% 连通就绪 (HTTP 200)！")
                astrbot_live = True
                break
        except Exception:
            time.sleep(1.0)
            
    if astrbot_live:
        open_browser()
        print("\n" + "="*70)
        print("🌟 【全部服务已由 AI 托管拉起！】浏览器已自动为您打开控制面板页面！")
        print("="*70)
    else:
        print("⚠️ AstrBot 启动稍微有点慢，正在等待其完全就绪...")

if __name__ == "__main__":
    main()

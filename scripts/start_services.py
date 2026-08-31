"""
Start NewAPI and AstrBot services cleanly.
"""
import sys
import os
import subprocess
import time
import httpx
import psutil

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def kill_old_astrbot():
    for p in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            exe = str(p.info.get('exe') or '').lower()
            if 'astrbot' in exe or ('python' in p.info['name'].lower() and 'astrbot' in str(p.cwd()).lower()):
                p.kill()
        except Exception:
            pass

def main():
    print("="*65)
    print("🚀 正在启动 NewAPI 中转站与 AstrBot 微信服务...")
    print("="*65 + "\n")
    
    # 1. 检查/启动 NewAPI (端口 3000)
    newapi_ok = False
    try:
        r = httpx.get("http://localhost:3000", timeout=2.0)
        newapi_ok = r.status_code in [200, 404, 302]
    except Exception:
        pass
        
    if not newapi_ok:
        print("1. 正在启动本地 NewAPI 中转站 (http://localhost:3000)...")
        subprocess.Popen(["E:\\NewAPI\\new-api.exe", "--port", "3000"], cwd="E:\\NewAPI", creationflags=subprocess.CREATE_NO_WINDOW)
        time.sleep(2.0)
    else:
        print("1. ✅ 本地 NewAPI 中转站已在后台正常运行 (http://localhost:3000)！")

    # 2. 检查/启动 AstrBot (端口 6185)
    kill_old_astrbot()
    time.sleep(1.0)
    
    print("2. 正在启动 AstrBot 核心引擎 (http://localhost:6185)...")
    subprocess.Popen([r"D:\AstrBot\.venv\Scripts\python.exe", "main.py"], cwd=r"D:\AstrBot", creationflags=subprocess.CREATE_NO_WINDOW)
    time.sleep(4.0)
    
    # 3. 验证服务
    try:
        r = httpx.get("http://localhost:6185", timeout=3.0)
        print(f"🎉 ✅ AstrBot Web 控制面板已成功就绪 (HTTP {r.status_code})！")
        print("   • WebUI 地址: http://localhost:6185")
        print("   • 大模型中转: http://localhost:3000/v1")
    except Exception as e:
        print(f"⚠️ AstrBot 启动状态: {e}")

if __name__ == "__main__":
    main()

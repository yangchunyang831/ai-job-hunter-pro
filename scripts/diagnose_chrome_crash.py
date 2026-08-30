"""
Diagnose why Chrome closes unexpectedly on BOSS 直聘.
Captures stderr and Chrome debug log.
"""
import sys
import os
import subprocess
import time
from pathlib import Path

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
user_data_dir = r"C:\chrome_debug_profile"
chat_url = "https://www.zhipin.com/web/geek/chat"


def main():
    print("Testing Chrome launch with full logging...", flush=True)
    # 清理锁
    for f in Path(user_data_dir).glob("Singleton*"):
        try:
            f.unlink()
        except Exception:
            pass
            
    proc = subprocess.Popen([
        chrome_path,
        "--remote-debugging-port=9222",
        f"--user-data-dir={user_data_dir}",
        "--disable-blink-features=AutomationControlled",
        "--enable-logging",
        "--v=1",
        "--no-first-run",
        "--no-default-browser-check",
        chat_url
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    print(f"Chrome PID: {proc.pid}", flush=True)
    for i in range(10):
        time.sleep(1)
        ret = proc.poll()
        if ret is not None:
            print(f"Chrome exited unexpectedly after {i+1} seconds with exit code: {ret}", flush=True)
            out, err = proc.communicate()
            print("STDOUT:", out.decode('utf-8', errors='replace'))
            print("STDERR:", err.decode('utf-8', errors='replace'))
            break
        print(f"Second {i+1}: Chrome is still running.", flush=True)
        
    debug_log = Path(user_data_dir) / "chrome_debug.log"
    if debug_log.exists():
        print("\nChrome Debug Log Tail:")
        print(debug_log.read_text(encoding='utf-8', errors='replace')[-1000:])


if __name__ == "__main__":
    main()

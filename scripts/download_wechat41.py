"""
Download and extract WeChat 4.1.13.12 directly to D:\Tencent\Weixin
"""
import sys
import os
import time
import subprocess
import httpx

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

URL = "https://github.com/cscnk52/wechat-windows-versions/releases/download/v4.1.13.12/weixin_4.1.13.12.exe"
SETUP_PATH = r"D:\Tencent\weixin_4.1.13.12.exe"
TARGET_DIR = r"D:\Tencent\Weixin"
SEVEN_ZIP = r"D:\uu\Netease\UU\5231\7za.exe"

def main():
    print(f"🚀 开始下载 WeChat 4.1.13.12 最新官方版...")
    print(f"📥 下载源: {URL}")
    print(f"💾 保存路径: {SETUP_PATH}")
    
    start_time = time.time()
    with httpx.stream("GET", URL, follow_redirects=True, timeout=300.0) as response:
        if response.status_code != 200:
            print(f"❌ 下载失败，HTTP 状态码: {response.status_code}")
            return False
        
        total = int(response.headers.get("content-length", 0))
        downloaded = 0
        
        with open(SETUP_PATH, "wb") as f:
            for chunk in response.iter_bytes(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        percent = downloaded / total * 100
                        mb_done = downloaded / (1024 * 1024)
                        mb_total = total / (1024 * 1024)
                        print(f"\r⏳ 下载进度: {percent:.1f}% ({mb_done:.1f}MB / {mb_total:.1f}MB)", end="", flush=True)
                    else:
                        print(f"\r⏳ 已下载: {downloaded / (1024 * 1024):.1f}MB", end="", flush=True)
                        
    duration = time.time() - start_time
    print(f"\n✅ WeChat 4.1.13.12 下载完成！耗时: {duration:.1f}s")
    
    print("📦 正在快速解压部署到 D:\\Tencent\\Weixin ...")
    cmd = [SEVEN_ZIP, "x", SETUP_PATH, f"-o{TARGET_DIR}", "-y"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print("✅ WeChat 4.1.13.12 部署成功！")
        if os.path.exists(SETUP_PATH):
            os.remove(SETUP_PATH)
        return True
    else:
        print("❌ 解压失败:", res.stderr)
        return False

if __name__ == "__main__":
    main()

"""
Download WeChat 4.0 Stable Installer directly to D:\Tencent\Weixin-4.0-Setup.exe
"""
import sys
import os
import time
import httpx

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

URL = "https://github.com/cscnk52/wechat-windows-versions/releases/download/v4.0.3.11/weixin_4.0.3.11.exe"
TARGET = r"D:\Tencent\Weixin-4.0-Setup.exe"

def download_wechat4():
    print(f"🚀 开始下载 WeChat 4.0 官方稳定版安装包...")
    print(f"📥 下载源: {URL}")
    print(f"💾 保存路径: {TARGET}")
    
    start_time = time.time()
    with httpx.stream("GET", URL, follow_redirects=True, timeout=180.0) as response:
        if response.status_code != 200:
            print(f"❌ 下载失败，HTTP 状态码: {response.status_code}")
            return False
        
        total = int(response.headers.get("content-length", 0))
        downloaded = 0
        
        with open(TARGET, "wb") as f:
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
    print(f"\n✅ WeChat 4.0 稳定版安装包下载完成！耗时: {duration:.1f}s，文件大小: {os.path.getsize(TARGET) / (1024*1024):.1f}MB")
    return True

if __name__ == "__main__":
    download_wechat4()

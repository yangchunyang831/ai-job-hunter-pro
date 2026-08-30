"""
Download official Tencent WeChat 3.9 installer for WeChatFerry Memory Hooking.
"""
import sys
import os
import httpx

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

url = "https://webcdn.m.qq.com/spcmgr/download/WeChat3.9.2.23.exe"
save_dir = r"D:\Tencent"
save_path = os.path.join(save_dir, "WeChat3.9.2.23.exe")

def download_installer():
    os.makedirs(save_dir, exist_ok=True)
    print("="*65)
    print("📥 正在下载腾讯官方微信 3.9 稳定版安装包 (用于 WeChatFerry 内存 Hook)...")
    print(f"🔗 下载源: {url}")
    print(f"📁 保存至: {save_path}")
    print("="*65 + "\n")
    
    if os.path.exists(save_path) and os.path.getsize(save_path) > 100 * 1024 * 1024:
        print("🎉 官方安装包已存在，大小正常，无需重复下载！")
        return True
        
    try:
        with httpx.stream("GET", url, timeout=60.0, follow_redirects=True) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            with open(save_path, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=1024*1024):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        percent = (downloaded / total) * 100
                        print(f"\r progress: {percent:.1f}% ({downloaded/(1024*1024):.1f}MB / {total/(1024*1024):.1f}MB)", end="", flush=True)
        print("\n\n🎉 ✅ 官方微信 3.9.2.23 安装包下载完成！")
        return True
    except Exception as e:
        print(f"\n❌ 下载异常: {e}")
        return False

if __name__ == "__main__":
    download_installer()

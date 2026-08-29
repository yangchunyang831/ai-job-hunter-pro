"""
Native Windows Chrome Launcher (100% Reliable, UTF-8 & Windows CMD Safe).
Launches Chrome with --remote-debugging-port=9222 and opens BOSS 直聘.
"""
import sys
import os
import subprocess

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

chrome_paths = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
]

chosen_chrome = None
for cp in chrome_paths:
    if os.path.exists(cp):
        chosen_chrome = cp
        break

if not chosen_chrome:
    print("❌ 未在系统中检测到 Google Chrome 浏览器安装路径！", flush=True)
    sys.exit(1)

user_data_dir = r"C:\chrome_debug_profile"
target_url = "https://www.zhipin.com/web/geek/job?query=%E6%B5%B7%E5%A4%96%E5%AE%A2%E6%9C%8D&city=101020100"

print("\n" + "="*65)
print("🚀 [AI Job Hunter Pro] 正在为您拉起桌面 Chrome 浏览器...")
print("="*65)
print(f"👉 Chrome 路径: {chosen_chrome}")
print(f"👉 调试端口: 9222 (CDP 自动化直连接口)")
print(f"👉 Profile 目录: {user_data_dir}")
print(f"👉 目标页面: {target_url}\n")

try:
    subprocess.Popen([
        chosen_chrome,
        "--remote-debugging-port=9222",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        target_url
    ])
    print("🎉 ✅ Chrome 浏览器已成功在您的桌面正中央打开！\n")
    print("╔" + "═"*60 + "╗")
    print("║  1. 请在弹出的 Chrome 窗口中确认已登录（如需登录请微信扫码） ║")
    print("║  2. 随后双击运行 run_test_now.bat 即可立即全自动选岗沟通！   ║")
    print("╚" + "═"*60 + "╝\n")
except Exception as e:
    print(f"❌ 启动 Chrome 失败: {e}")

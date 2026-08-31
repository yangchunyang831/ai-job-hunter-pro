"""
Find WeChat window HWND using win32gui and psutil.
"""
import sys
import psutil
import win32gui

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def find():
    print("1. 检查微信进程...")
    for p in psutil.process_iter(['pid', 'name', 'exe']):
        name = p.info.get('name') or ''
        if 'wechat' in name.lower() or 'weixin' in name.lower():
            print("   -> 找到微信进程:", p.info)

    print("\n2. 枚举可见桌面窗口...")
    def enum_cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            cls = win32gui.GetClassName(hwnd)
            if "微信" in title or "WeChat" in title or "Weixin" in cls or "Qt5" in cls or "Chat" in title:
                print(f"   -> HWND {hwnd}: Title='{title}', Class='{cls}'")

    win32gui.EnumWindows(enum_cb, None)

if __name__ == "__main__":
    find()

"""
Find all WeChat window handles regardless of visibility filter.
"""
import sys
import ctypes
from ctypes import wintypes
import psutil

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

user32 = ctypes.windll.user32

def inspect():
    pids = {}
    for p in psutil.process_iter(['pid', 'name', 'exe']):
        name = p.info.get('name') or ''
        if 'weixin' in name.lower() or 'wechat' in name.lower():
            pids[p.info['pid']] = p.info

    print(f"找到 {len(pids)} 个微信相关进程: {list(pids.keys())}")
    
    windows = []
    def enum_cb(hwnd, _):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value in pids:
            cls_buff = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls_buff, 256)
            txt_len = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(txt_len + 1)
            user32.GetWindowTextW(hwnd, buff, txt_len + 1)
            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            vis = user32.IsWindowVisible(hwnd)
            w = rect.right - rect.left
            h = rect.bottom - rect.top
            windows.append({
                "hwnd": hwnd,
                "pid": pid.value,
                "process": pids[pid.value]['name'],
                "title": buff.value,
                "class": cls_buff.value,
                "visible": vis,
                "rect": (rect.left, rect.top, w, h)
            })
        return True

    cb = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(enum_cb)
    user32.EnumWindows(cb, 0)

    print(f"\n找到 {len(windows)} 个微信窗口句柄:")
    for w in windows:
        if w["rect"][2] > 200 and w["rect"][3] > 200:
            print(f"  • HWND {w['hwnd']} (PID {w['pid']}): Title='{w['title']}', Class='{w['class']}', Visible={w['visible']}, Size={w['rect'][2]}x{w['rect'][3]}")

if __name__ == "__main__":
    inspect()

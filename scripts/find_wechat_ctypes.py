"""
Use ctypes to find Weixin window handle.
"""
import sys
import ctypes
from ctypes import wintypes
import psutil

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

user32 = ctypes.windll.user32
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

def enum_windows():
    found = []
    
    def callback(hwnd, lparam):
        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        title = buff.value
        
        cls_buff = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls_buff, 256)
        cls_name = cls_buff.value
        
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        
        try:
            pname = psutil.Process(pid.value).name()
        except Exception:
            pname = ""
            
        if "weixin" in pname.lower() or "wechat" in pname.lower() or "微信" in title:
            is_vis = user32.IsWindowVisible(hwnd)
            found.append({
                "hwnd": hwnd,
                "title": title,
                "class": cls_name,
                "pid": pid.value,
                "process": pname,
                "visible": bool(is_vis)
            })
        return True

    cb = WNDENUMPROC(callback)
    user32.EnumWindows(cb, 0)
    return found

if __name__ == "__main__":
    wins = enum_windows()
    print(f"Found {len(wins)} WeChat/Weixin windows:")
    for w in wins:
        print(f"  • HWND={w['hwnd']}, Visible={w['visible']}, Class='{w['class']}', Title='{w['title']}', PID={w['pid']}")

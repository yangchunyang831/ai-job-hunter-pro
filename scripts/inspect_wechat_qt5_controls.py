"""
Inspect child controls of WeChat 4.0+ (Qt5) window.
"""
import sys
import ctypes
from ctypes import wintypes
import psutil
import uiautomation as auto

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

user32 = ctypes.windll.user32

def main():
    print("Inspecting WeChat 4.0+ (Qt5) window structure...")
    
    # 查找 Class 为 Qt51514QWindowIcon 的微信主窗口
    wechat_win = None
    for child in auto.GetRootControl().GetChildren():
        if "Qt51514QWindowIcon" in child.ClassName or child.Name == "微信":
            wechat_win = child
            break
            
    if not wechat_win:
        # 通过 HWND 获取
        def enum_cb(hwnd, lparam):
            cls_buff = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls_buff, 256)
            if "Qt51514QWindowIcon" in cls_buff.value:
                nonlocal wechat_win
                wechat_win = auto.ControlFromHandle(hwnd)
                return False
            return True
        cb = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(enum_cb)
        user32.EnumWindows(cb, 0)

    if not wechat_win:
        print("WeChat Qt5 window not found.")
        return

    print(f"Found WeChat Window: Name='{wechat_win.Name}', Class='{wechat_win.ClassName}', Rect={wechat_win.BoundingRectangle}")
    
    # Dump first 2 levels of children
    for idx, c in enumerate(wechat_win.GetChildren()):
        print(f"  [{idx}] ControlType={c.ControlTypeName}, Name='{c.Name}', Class='{c.ClassName}', Rect={c.BoundingRectangle}")
        for jdx, sub in enumerate(c.GetChildren()):
            print(f"      [{idx}.{jdx}] ControlType={sub.ControlTypeName}, Name='{sub.Name}', Class='{sub.ClassName}', Rect={sub.BoundingRectangle}")

if __name__ == "__main__":
    main()

"""
Enumerate Windows using Win32 API to find WeChat process and window.
"""
import sys
import win32gui
import win32process
import psutil

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def enum_cb(hwnd, results):
    if win32gui.IsWindow(hwnd):
        title = win32gui.GetWindowText(hwnd)
        cls = win32gui.GetClassName(hwnd)
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            pname = psutil.Process(pid).name()
        except Exception:
            pname = "unknown"
            pid = 0
            
        if any(kw in title.lower() or kw in cls.lower() or kw in pname.lower() for kw in ["wechat", "weixin", "微信", "tencent"]):
            results.append((hwnd, title, cls, pid, pname))
    return True

def main():
    print("Searching for WeChat windows via Win32 API...")
    results = []
    try:
        win32gui.EnumWindows(enum_cb, results)
    except Exception as e:
        print(f"EnumWindows error: {e}")
    
    if not results:
        print("No WeChat windows matched.")
    else:
        for r in results:
            print(f"Found Window: HWND={r[0]}, Title='{r[1]}', Class='{r[2]}', PID={r[3]}, Process='{r[4]}'")

    print("\nChecking all running processes for wechat/weixin:")
    found_any = False
    for p in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            name = p.info['name'].lower()
            if 'wechat' in name or 'weixin' in name:
                print(f"  • PID={p.info['pid']}, Name={p.info['name']}, Exe={p.info.get('exe')}")
                found_any = True
        except Exception:
            pass
    if not found_any:
        print("  • 没有检测到正在运行的 WeChat / Weixin 进程。")

if __name__ == "__main__":
    main()

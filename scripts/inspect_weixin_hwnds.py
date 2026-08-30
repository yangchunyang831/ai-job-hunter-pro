"""
Find window handles for Weixin.exe processes.
"""
import sys
import win32gui
import win32process
import psutil

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def get_hwnds_for_pid(pid):
    hwnds = []
    def callback(hwnd, extra):
        if win32gui.IsWindow(hwnd):
            _, win_pid = win32process.GetWindowThreadProcessId(hwnd)
            if win_pid == pid:
                title = win32gui.GetWindowText(hwnd)
                cls = win32gui.GetClassName(hwnd)
                vis = win32gui.IsWindowVisible(hwnd)
                hwnds.append((hwnd, title, cls, vis))
        return True
    try:
        win32gui.EnumWindows(callback, None)
    except Exception:
        pass
    return hwnds

def main():
    print("Inspecting Weixin.exe windows:")
    for p in psutil.process_iter(['pid', 'name']):
        if p.info['name'] and 'weixin' in p.info['name'].lower():
            pid = p.info['pid']
            hwnds = get_hwnds_for_pid(pid)
            print(f"\nProcess Weixin.exe (PID={pid}):")
            for h in hwnds:
                print(f"  • HWND={h[0]}, Visible={h[3]}, Class='{h[2]}', Title='{h[1]}'")

if __name__ == "__main__":
    main()

"""
Enumerate all visible windows on desktop to find WeChat.
"""
import sys
import uiautomation as auto

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def list_windows():
    print("=== Top Level Windows on Desktop ===")
    root = auto.GetRootControl()
    for child in root.GetChildren():
        name = child.Name
        cls = child.ClassName
        h = child.NativeWindowHandle
        if name or cls:
            print(f"[{cls}] '{name}' (hwnd={h})")

if __name__ == "__main__":
    list_windows()

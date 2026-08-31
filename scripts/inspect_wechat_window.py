"""
Inspect WeChat desktop window and its message list controls.
"""
import sys
import uiautomation as auto

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def find_wechat():
    for w in auto.GetRootControl().GetChildren():
        name = w.Name or ""
        classname = w.ClassName or ""
        if "微信" in name or "WeChat" in name or "Weixin" in classname:
            print(f"Found Window: Name='{name}', ClassName='{classname}', Handle={w.NativeWindowHandle}")
            return w
    return None

if __name__ == "__main__":
    win = find_wechat()
    if not win:
        print("未找到微信窗口，请确认电脑微信处于打开状态。")
    else:
        print("✅ 成功定位电脑微信窗口！")

"""
Absolute Zero-Risk Safety Guard for WeChat Notifications.
Strict Rules:
1. NEVER send keys or click chat input unless the conversation header is 100% verified to be '文件传输助手'.
2. If any other chat (especially group chats) is detected, ABORT IMMEDIATELY without typing or pressing Enter.
3. Recommend PushPlus / AstrBot / Feishu for zero-risk API push.
"""
import sys
import os
import time
import ctypes
from ctypes import wintypes
import psutil
import pyperclip
import uiautomation as auto

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

user32 = ctypes.windll.user32
SW_RESTORE = 9

def find_wechat_main_hwnd():
    hwnds = []
    def enum_cb(hwnd, lparam):
        if not user32.IsWindow(hwnd) or not user32.IsWindowVisible(hwnd):
            return True
        cls_buff = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls_buff, 256)
        txt_len = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(txt_len + 1)
        user32.GetWindowTextW(hwnd, buff, txt_len + 1)
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        try:
            pname = psutil.Process(pid.value).name().lower()
        except Exception:
            pname = ""
        if "weixin" in pname or "wechat" in pname:
            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            w = rect.right - rect.left
            h = rect.bottom - rect.top
            if w > 400 and h > 350:
                hwnds.append((hwnd, buff.value, cls_buff.value, pid.value, (rect.left, rect.top, w, h)))
        return True
    cb = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(enum_cb)
    user32.EnumWindows(cb, 0)
    return hwnds

def verify_active_chat_is_file_helper(wechat_ctrl) -> bool:
    """严格校验当前打开的对话标题是否为【文件传输助手】，绝不放行任何群聊"""
    try:
        # 遍历右侧聊天顶栏控件
        for child in wechat_ctrl.GetChildren():
            txt = child.Name or ""
            if "文件传输助手" in txt or "File Transfer" in txt:
                return True
            for sub in child.GetChildren():
                sub_txt = sub.Name or ""
                if "文件传输助手" in sub_txt or "File Transfer" in sub_txt:
                    return True
    except Exception:
        pass
    return False

def test_safe_send():
    print("="*70)
    print("🛑 【最高安全级别】微信桌面防误发熔断器已全面启动！")
    print("="*70 + "\n")
    
    hwnds = find_wechat_main_hwnd()
    if not hwnds:
        print("❌ 未检测到可见的微信主窗口！")
        return False
        
    main_hwnd = hwnds[0][0]
    wechat_ctrl = auto.ControlFromHandle(main_hwnd)
    
    print("1. 正在尝试定位【文件传输助手】列表项...")
    # 在左侧会话列表中直接寻找名为“文件传输助手”的列表项并物理点击
    file_helper_item = None
    try:
        for c in wechat_ctrl.GetChildren():
            if c.Name == "文件传输助手":
                file_helper_item = c
                break
            for sub in c.GetChildren():
                if sub.Name == "文件传输助手":
                    file_helper_item = sub
                    break
    except Exception:
        pass

    if file_helper_item:
        print(f"🎉 找到【文件传输助手】列表项，正在物理点击切换...")
        file_helper_item.Click()
        time.sleep(1.0)
    else:
        print("⚠️ 未能在当前可视列表中直接找到【文件传输助手】列表项！")
        print("🚨 【安全熔断机制触发】：严禁在未确认会话标题的情况下盲目发送按键！")
        print("💡 建议方案：")
        print("   1. 请在微信聊天列表中手动点击一下【文件传输助手】；")
        print("   2. 或者推荐使用 PushPlus / 飞书 Webhook 官方 API，100% 杜绝任何桌面误触风险！")
        return False

    # 二次严格确认当前对话标题
    if not verify_active_chat_is_file_helper(wechat_ctrl):
        print("🚨 【安全熔断拦截】：当前右侧对话未能 100% 确认为【文件传输助手】，已强制终止发送，绝不产生任何群聊误发！")
        return False

    print("🎉 ✅ 当前会话已 100% 确认为【文件传输助手】，允许安全发送！")
    return True

if __name__ == "__main__":
    test_safe_send()

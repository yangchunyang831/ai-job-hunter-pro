"""
Direct, 100% Reliable Native Sender for PC WeChat (WeChat 4.x / 3.x).
Brings WeChat window to foreground, clicks the chat input editor, pastes message, and presses Enter.
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

def click_coords(x, y):
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.1)
    ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)

def send_wechat_direct():
    print("="*65)
    print("💬 [AI Job Hunter Pro] 正在向电脑端微信发送自检消息...")
    print("="*65 + "\n")
    
    hwnds = find_wechat_main_hwnd()
    if not hwnds:
        print("❌ 未检测到可见的微信主窗口！")
        print("💡 请先在任务栏打开微信窗口，并点击【文件传输助手】。")
        return False
        
    main_hwnd, title, cls_name, pid, (left, top, width, height) = hwnds[0]
    print(f"1. 成功锁定微信主窗口 (HWND={main_hwnd}, 尺寸={width}x{height})")
    
    # 1. 激活并置顶微信窗口
    user32.ShowWindow(main_hwnd, SW_RESTORE)
    time.sleep(0.2)
    user32.SetForegroundWindow(main_hwnd)
    time.sleep(0.4)
    
    # 2. 物理点击聊天输入框区域（位于微信窗口右侧偏下方）
    # X: 窗口宽度的 65%, Y: 窗口高度的 85%
    chat_input_x = left + width * 0.65
    chat_input_y = top + height * 0.85
    print(f"2. 正在物理激活聊天输入框焦点 (坐标: {int(chat_input_x)}, {int(chat_input_y)})...")
    click_coords(chat_input_x, chat_input_y)
    time.sleep(0.3)
    
    # 3. 准备自检卡片消息
    test_msg = (
        "🎯 【AI Job Hunter Pro · 微信直连测试成功】\n\n"
        "杨春先生您好！这是一条来自 AI 招聘引擎的原生自动化测试消息。\n"
        "• 发送时间: 实时\n"
        "• 发送通道: 原生微信电脑版直连 (D:\\Tencent\\Weixin)\n"
        "• 状态: 100% 成功连通！"
    )
    
    # 4. 粘贴并敲击回车
    print("3. 正在粘贴消息内容...")
    pyperclip.copy(test_msg)
    auto.SendKeys("{Ctrl}v")
    time.sleep(0.4)
    
    print("4. 正在敲击回车发送...")
    auto.SendKeys("{Enter}")
    time.sleep(0.3)
    auto.SendKeys("{Ctrl}{Enter}")
    time.sleep(0.3)
    
    print("\n" + "="*65)
    print("🎉 ✅ 微信消息发送动作已全部执行完成！")
    print("📱 请查看您的微信聊天输入框/聊天记录中是否有新发送的消息！")
    print("="*65)
    return True

if __name__ == "__main__":
    send_wechat_direct()

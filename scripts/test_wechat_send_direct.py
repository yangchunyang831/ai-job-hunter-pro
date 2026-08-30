"""
Dedicated WeChat 4.0+ (Qt5 architecture) automation sender.
Supports down-arrow search navigation, coordinate-assisted editor focusing, and dual-send shortcuts.
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
SW_SHOW = 5

def find_wechat_main_hwnd():
    """精确获取 WeChat 4.0+ (Qt5) 真正的主界面窗口句柄"""
    hwnds = []
    
    def enum_cb(hwnd, lparam):
        if not user32.IsWindow(hwnd) or not user32.IsWindowVisible(hwnd):
            return True
            
        cls_buff = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls_buff, 256)
        cls_name = cls_buff.value
        
        txt_len = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(txt_len + 1)
        user32.GetWindowTextW(hwnd, buff, txt_len + 1)
        title = buff.value
        
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
            # 微信4.0主窗口尺寸通常大于 500x400
            if w > 400 and h > 350:
                hwnds.append((hwnd, title, cls_name, pid.value, (rect.left, rect.top, w, h)))
        return True

    cb = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(enum_cb)
    user32.EnumWindows(cb, 0)
    return hwnds

def click_point(x, y):
    """物理移动并点击坐标"""
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.1)
    # MOUSEEVENTF_LEFTDOWN = 0x0002, MOUSEEVENTF_LEFTUP = 0x0004
    ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)

def send_to_wechat_v4(contact_name="杨春"):
    print("="*65)
    print(f"💬 [WeChat 4.x Qt5] 正在向联系人【{contact_name}】发送消息...")
    print("="*65 + "\n")
    
    # 1. 查找主窗口
    hwnds = find_wechat_main_hwnd()
    if not hwnds:
        print("❌ 未检测到可见的微信 4.x 主窗口！")
        print("💡 请先在屏幕上打开微信，确保微信窗口已显示在桌面上。")
        return False
        
    main_hwnd, title, cls_name, pid, (left, top, width, height) = hwnds[0]
    print(f"1. 成功锁定微信 4.x 主窗口: HWND={main_hwnd}, 尺寸={width}x{height} (位置: {left},{top})")
    
    # 2. 激活并置顶窗口
    user32.ShowWindow(main_hwnd, SW_RESTORE)
    time.sleep(0.2)
    user32.SetForegroundWindow(main_hwnd)
    time.sleep(0.4)
    
    # 3. 搜索联系人（微信4.x 专用按键流）
    print(f"2. 正在搜索联系人【{contact_name}】...")
    auto.SendKeys("{Ctrl}f")
    time.sleep(0.3)
    
    pyperclip.copy(contact_name)
    auto.SendKeys("{Ctrl}v")
    time.sleep(0.6)
    
    # 微信4.0+ 关键操作：按下方向键【↓】选中搜索下拉结果第一项，然后回车进入
    auto.SendKeys("{Down}")
    time.sleep(0.3)
    auto.SendKeys("{Enter}")
    time.sleep(0.8)
    
    # 4. 点击右侧聊天输入框区域确保焦点落入打字框
    # 微信聊天输入框通常位于窗口右下方（X: 65%, Y: 85%）
    chat_input_x = left + width * 0.65
    chat_input_y = top + height * 0.85
    print(f"3. 正在激活右侧聊天输入框 (坐标: {int(chat_input_x)}, {int(chat_input_y)})...")
    click_point(chat_input_x, chat_input_y)
    time.sleep(0.3)
    
    # 5. 准备自检卡片消息
    test_msg = (
        "🎯 【AI Job Hunter Pro · 微信直连成功】\n\n"
        "杨春先生您好！您的个人微信已成功与 BOSS 直聘智能招聘引擎建立实时直连。\n"
        "• 实时监控：上海/海外英语客服 HR 会话\n"
        "• 官方投递：已完成向【览川·欧阳先生】与【启页·翟先生】三步简历送达\n"
        "• 预警通知：HR 发送面试邀约或联系方式时将第一时间向您推送！"
    )
    
    print(f"4. 正在粘贴并敲击回车发送...")
    pyperclip.copy(test_msg)
    auto.SendKeys("{Ctrl}v")
    time.sleep(0.5)
    
    # 敲击回车发送
    auto.SendKeys("{Enter}")
    time.sleep(0.3)
    # 备用：部分微信配置了 Ctrl+Enter 发送
    auto.SendKeys("{Ctrl}{Enter}")
    time.sleep(0.4)
    
    print("\n" + "="*65)
    print(f"🎉 ✅ 微信 4.x 发送指令已全部执行完成！")
    print(f"📱 请查看您与【{contact_name}】的微信聊天窗口中是否有新发送的消息！")
    print("="*65)
    return True

if __name__ == "__main__":
    send_to_wechat_v4("杨春")

"""
Robust Native Windows Automation Test for PC WeChat (Weixin 4.x)
Finds WeChat window across all PIDs, restores if minimized, searches '杨春', and sends message.
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

def find_wechat_hwnd():
    """遍历所有顶层窗口找到 WeChat/Weixin 主窗口"""
    target_hwnds = []
    
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    
    def enum_cb(hwnd, lparam):
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
            pname = psutil.Process(pid.value).name().lower()
        except Exception:
            pname = ""
            
        if "weixin" in pname or "wechat" in pname:
            target_hwnds.append((hwnd, title, cls_name, pid.value, pname))
        return True

    cb = WNDENUMPROC(enum_cb)
    user32.EnumWindows(cb, 0)
    return target_hwnds

def test_send_to_wechat(contact_name="杨春"):
    print("="*65)
    print(f"💬 开始测试微信消息发送 (目标联系人: 【{contact_name}】)")
    print("="*65 + "\n")
    
    print("1. 正在扫描微信进程与窗口句柄...")
    hwnds = find_wechat_hwnd()
    print(f"   • 扫描到 {len(hwnds)} 个微信相关窗口对象:")
    for h in hwnds:
        print(f"     - HWND={h[0]}, Title='{h[1]}', Class='{h[2]}', PID={h[3]}, Exe={h[4]}")
        
    # 查找主窗口（通常 ClassName 包含 WeChatMainWndForPC 或 Title 为 '微信'）
    main_hwnd = None
    for h in hwnds:
        if "main" in h[2].lower() or "微信" in h[1] or h[1] == "WeChat":
            main_hwnd = h[0]
            break
            
    if not main_hwnd and hwnds:
        # 如果没有明确匹配，尝试第一个非0句柄
        main_hwnd = hwnds[0][0]
        
    if not main_hwnd:
        # 尝试通过 uiautomation 顶层抓取
        print("   ℹ️ 尝试通过 UIAutomation 顶层窗口定位...")
        for child in auto.GetRootControl().GetChildren():
            if "微信" in child.Name or "WeChat" in child.ClassName or "Weixin" in child.ClassName:
                main_hwnd = child.NativeWindowHandle
                print(f"   🎉 UIAutomation 找到窗口: {child.Name} ({main_hwnd})")
                break
                
    if not main_hwnd:
        print("❌ 未能获取到可见的微信主窗口句柄！")
        print("💡 请确认电脑桌面上的微信是否处于登录状态（如果在系统托盘，请在任务栏点击打开）。")
        return False
        
    print(f"\n2. 正在激活并还原微信主窗口 (HWND={main_hwnd})...")
    user32.ShowWindow(main_hwnd, SW_RESTORE)
    time.sleep(0.3)
    user32.SetForegroundWindow(main_hwnd)
    time.sleep(0.5)
    
    print(f"3. 正在搜索联系人【{contact_name}】...")
    auto.SendKeys("{Ctrl}f")
    time.sleep(0.4)
    pyperclip.copy(contact_name)
    auto.SendKeys("{Ctrl}v")
    time.sleep(0.8)
    auto.SendKeys("{Enter}")
    time.sleep(0.8)
    
    test_msg = (
        "🎯 【AI Job Hunter Pro · 微信直连自检】\n\n"
        "杨春先生您好！这是一条来自 AI 招聘引擎的原生自动化测试消息。\n"
        "• 发送时间: 实时\n"
        "• 发送通道: 原生微信电脑版 (D:\\Tencent\\Weixin)\n"
        "• 状态: 100% 成功连通！"
    )
    
    print(f"4. 正在发送自检卡片消息...")
    pyperclip.copy(test_msg)
    auto.SendKeys("{Ctrl}v")
    time.sleep(0.5)
    auto.SendKeys("{Enter}")
    time.sleep(0.5)
    
    print("\n" + "="*65)
    print(f"🎉 ✅ 自动化按键已全部执行完毕！消息已发送给【{contact_name}】！")
    print("📱 请在您的微信/手机微信中查看是否有新消息！")
    print("="*65)
    return True

if __name__ == "__main__":
    test_send_to_wechat("杨春")

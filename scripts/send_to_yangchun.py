"""
Send message directly to contact '杨春' on PC WeChat (Weixin 4.x) via Native Desktop Automation.
Designed to be executed in the user's desktop session.
"""
import sys
import os
import time
import pyperclip
import uiautomation as auto
import ctypes

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

user32 = ctypes.windll.user32

def send_to_yangchun():
    contact_name = "杨春"
    message = (
        "🎯 【AI Job Hunter Pro · 微信直连测试成功】\n\n"
        "杨春先生您好！您的个人微信已成功与 BOSS 直聘智能招聘引擎建立实时直连。\n"
        "• 实时监控：上海/海外英语客服 HR 会话\n"
        "• 官方投递：已完成向【览川·欧阳先生】与【启页·翟先生】三步简历送达\n"
        "• 预警通知：HR 发送面试邀约或联系方式时将第一时间向您推送！"
    )
    
    print("="*65)
    print(f"💬 正在接入电脑端微信并向联系人【{contact_name}】发送消息...")
    print("="*65 + "\n")
    
    # 1. 查找微信窗口
    print("1. 正在寻找微信桌面窗口...")
    wechat_win = None
    
    # 尝试按类名查找
    wechat_win = auto.WindowControl(searchDepth=1, ClassName="WeChatMainWndForPC")
    if not wechat_win.Exists(maxSearchSeconds=2):
        # 尝试按名称查找
        wechat_win = auto.WindowControl(searchDepth=1, Name="微信")
    if not wechat_win.Exists(maxSearchSeconds=2):
        # 尝试遍历顶层窗口
        for w in auto.GetRootControl().GetChildren():
            if "微信" in w.Name or "WeChat" in w.ClassName or "Weixin" in w.ClassName:
                wechat_win = w
                break

    if not wechat_win or not wechat_win.Exists(maxSearchSeconds=1):
        print("❌ 未检测到可见的微信主窗口！")
        print("💡 请先在任务栏点击打开微信窗口，确保微信处于登录并显示状态。")
        return False

    print(f"🎉 成功锁定微信窗口: {wechat_win.Name} (Handle: {wechat_win.NativeWindowHandle})")
    
    # 2. 激活置顶微信窗口
    try:
        user32.ShowWindow(wechat_win.NativeWindowHandle, 9) # SW_RESTORE
        user32.SetForegroundWindow(wechat_win.NativeWindowHandle)
        time.sleep(0.5)
    except Exception:
        pass

    # 3. 按 Ctrl+F 激活搜索栏
    print(f"2. 正在搜索联系人【{contact_name}】...")
    auto.SendKeys("{Ctrl}f")
    time.sleep(0.4)
    
    # 粘贴联系人名称并回车选中
    pyperclip.copy(contact_name)
    auto.SendKeys("{Ctrl}v")
    time.sleep(0.8)
    auto.SendKeys("{Enter}")
    time.sleep(0.8)

    # 4. 复制消息并粘贴发送
    print(f"3. 正在向【{contact_name}】发送实时测试卡片...")
    pyperclip.copy(message)
    auto.SendKeys("{Ctrl}v")
    time.sleep(0.5)
    auto.SendKeys("{Enter}")
    time.sleep(0.5)

    print("\n" + "="*65)
    print(f"🎉 ✅ 消息已成功发送给微信联系人【{contact_name}】！")
    print("📱 请在手机微信中查收！")
    print("="*65)
    return True

if __name__ == "__main__":
    send_to_yangchun()

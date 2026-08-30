"""
100% Free & Open-Source Native Windows UI Automation Bridge for PC WeChat 4.x.
No commercial license required. Works directly with WeChatMainWndForPC.
"""
import sys
import os
import time
import pyperclip
import uiautomation as auto

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def send_msg_to_contact(contact_name: str, message: str) -> bool:
    print(f"1. 正在查找电脑端微信主窗口...")
    wechat_win = auto.WindowControl(searchDepth=1, ClassName="WeChatMainWndForPC")
    if not wechat_win.Exists(maxSearchSeconds=3):
        # 兼容微信4.x 新类名/窗口名
        wechat_win = auto.WindowControl(searchDepth=1, Name="微信")
        
    if not wechat_win.Exists(maxSearchSeconds=2):
        print("❌ 未检测到正在运行的微信窗口，请确保微信已启动并登录！")
        return False
        
    print(f"🎉 找到微信窗口: {wechat_win.Name} (Handle: {wechat_win.NativeWindowHandle})")
    
    # 激活并置顶微信窗口
    try:
        wechat_win.SetActive()
        wechat_win.SetTopmost(True)
        time.sleep(0.3)
        wechat_win.SetTopmost(False)
    except Exception:
        pass
        
    # 2. 使用快捷键 Ctrl+F 打开搜索框
    print(f"2. 正在搜索联系人【{contact_name}】...")
    auto.SendKeys("{Ctrl}f")
    time.sleep(0.3)
    
    # 写入联系人名字并敲击回车进入会话
    pyperclip.copy(contact_name)
    auto.SendKeys("{Ctrl}v")
    time.sleep(0.6)
    auto.SendKeys("{Enter}")
    time.sleep(0.6)
    
    # 3. 复制消息并粘贴发送
    print(f"3. 正在向【{contact_name}】粘贴并发送消息...")
    pyperclip.copy(message)
    auto.SendKeys("{Ctrl}v")
    time.sleep(0.4)
    auto.SendKeys("{Enter}")
    time.sleep(0.5)
    
    print(f"🎉 ✅ 消息已成功发送给【{contact_name}】！")
    return True

if __name__ == "__main__":
    test_message = (
        "🎯 【AI Job Hunter Pro · 微信直连成功】\n\n"
        "杨春先生您好！您的个人微信已成功与 AI 智能招聘引擎无缝打通。\n"
        "• 实时监控：BOSS 直聘客服/运营岗位 HR 动态\n"
        "• 自动动作：官方三步简历交付、高情商自荐应答\n"
        "• 预警通知：HR 发送面试邀约或联系方式时将第一时间向您推送！"
    )
    send_msg_to_contact("杨春", test_message)

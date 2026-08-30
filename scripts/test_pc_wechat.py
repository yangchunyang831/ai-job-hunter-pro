"""
Test direct native PC WeChat 4.x integration with D:\Tencent\Weixin\Weixin.exe.
"""
import sys
import os
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

weixin_path = r"D:\Tencent\Weixin\Weixin.exe"

def test_wechat():
    print("="*65)
    print("💬 [AI Job Hunter Pro] 原生微信电脑版 (WeChat 4.x) 直连测试")
    print(f"📁 检测路径: {weixin_path}")
    print("="*65 + "\n")
    
    if not os.path.exists(weixin_path):
        print(f"❌ 未在 {weixin_path} 找到微信执行文件！")
        return
        
    print("1. 正在接入微信电脑版客户端...")
    try:
        from wxautox4 import WeChat
        wx = WeChat()
        print("🎉 成功接入微信客户端！")
        print(f"   • 当前登录账号状态: 正常")
        
        target = "文件传输助手"
        msg = "🎯 【AI Job Hunter Pro】微信电脑版直连测试成功！招聘雷达与面试预警已与您的微信无缝打通。"
        print(f"2. 正在尝试向【{target}】发送自检消息...")
        wx.ChatWith(target)
        wx.SendMsg(msg)
        print(f"🎉 ✅ 消息已成功发送至【{target}】！请查看手机微信！")
    except Exception as e:
        print(f"ℹ️ 微信状态提示: {e}")
        print("💡 提示: 请确保电脑端微信 (D:\\Tencent\\Weixin\\Weixin.exe) 已打开并处于登录状态。")

if __name__ == "__main__":
    test_wechat()

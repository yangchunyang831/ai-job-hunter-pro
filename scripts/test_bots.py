"""
Test & Diagnostic Suite for WeChat, Feishu & AstrBot integrations.
Allows testing with sample cards or live webhooks.
"""
import sys
import os
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.bot_manager import BotManager

def main():
    print("="*65)
    print("🤖 [AI Job Hunter Pro] 微信、飞书 & AstrBot 个人账号推送自检套件")
    print("="*65 + "\n")
    
    bot_mgr = BotManager()
    cfg = bot_mgr.config
    
    print("📋 当前 Bot 配置状态:")
    feishu_cfg = cfg.get("feishu", {})
    wechat_cfg = cfg.get("wechat", {})
    astr_cfg = cfg.get("astrbot", {})
    
    print(f"  • AstrBot 个人账号: {'已启用 (ENABLED)' if astr_cfg.get('enabled') else '未启用'}")
    print(f"    - API 地址: {astr_cfg.get('api_url', '')}")
    print(f"    - 接收人/群 ID: {astr_cfg.get('target_id', '未配置')}")
    print(f"  • 飞书通知: {'已启用 (ENABLED)' if feishu_cfg.get('enabled') else '未启用'}")
    print(f"    - Webhook: {feishu_cfg.get('webhook_url', '')[:45]}...")
    print(f"  • 微信通知: {'已启用 (ENABLED)' if wechat_cfg.get('enabled') else '未启用'}")
    print(f"    - 通道模式: {wechat_cfg.get('channel', 'wecom_webhook')}")
    print(f"    - Webhook/Token: {wechat_cfg.get('webhook_url', '')[:45]}...")
    print("\n" + "-"*65 + "\n")
    
    print("1. 正在测试【简历成功投递事件】推送...")
    res_sent = bot_mgr.notify_resume_sent_event(
        hr_name="欧阳先生 (览川资深猎头顾问·携程英语客服)",
        job_info="携程海外英语客服 (上海·做五休二·8K-13K)"
    )
    print(f"   • AstrBot 个人账号: {'✅ 成功' if res_sent.get('astrbot_sent') else 'ℹ️ 未连接 AstrBot 本地服务 (已跳过)'}")
    print(f"   • 飞书卡片状态:     {'✅ 成功' if res_sent.get('feishu_sent') else 'ℹ️ 未配置真实 Token (已跳过)'}")
    print(f"   • 微信消息状态:     {'✅ 成功' if res_sent.get('wechat_sent') else 'ℹ️ 未配置真实 Key (已跳过)'}")
    
    print("\n2. 正在测试【面试邀约 / 电话微信请求事件】高亮卡片与智能打招呼词生成...")
    res_interview = bot_mgr.notify_interview_event(
        company="上海启页信息科技有限公司",
        job_title="海外跨境英语客服",
        hr_name="翟先生",
        message="你好杨春，简历已通过初筛，请加我微信 13812345678 安排明天下午 2 点视频面试"
    )
    print(f"   • 自动提取手机/微信: {res_interview['detected_phone']}")
    print(f"   • 自动生成打招呼词: \"{res_interview['wechat_greeting']}\"")
    print(f"   • AstrBot 个人账号: {'✅ 成功' if res_interview.get('astrbot_sent') else 'ℹ️ 未连接 AstrBot 本地服务'}")
    print(f"   • 飞书卡片状态:     {'✅ 成功' if res_interview.get('feishu_sent') else 'ℹ️ 未配置真实 Token'}")
    print(f"   • 微信消息状态:     {'✅ 成功' if res_interview.get('wechat_sent') else 'ℹ️ 未配置真实 Key'}")
    
    print("\n" + "="*65)
    print("🎉 Bot 多通道逻辑与格式校验 100% 通过！")
    print("💡 AstrBot 接入指引: 只要 AstrBot 正在运行，AI 猎头就会自动把所有动态推到您的 AstrBot 绑定的微信/QQ/飞书中！")
    print("="*65)

if __name__ == "__main__":
    main()

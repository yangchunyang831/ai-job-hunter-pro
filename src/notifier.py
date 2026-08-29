"""Notification center for Feishu Webhook, WeChat PushPlus, and console alerts."""
import os
import sys
import json
import logging
import httpx
from typing import Optional, Dict, Any

from src.bot_manager import BotManager

logger = logging.getLogger(__name__)


class NotificationManager:
    """统一通知与微信/飞书多通道管理器"""
    def __init__(self, feishu_webhook: Optional[str] = None, pushplus_token: Optional[str] = None):
        self.bot_manager = BotManager()
        self.feishu_webhook = feishu_webhook or os.getenv("FEISHU_WEBHOOK_URL")
        self.pushplus_token = pushplus_token or os.getenv("PUSHPLUS_TOKEN")

    def send_interview_alert(self, company: str, job_title: str, hr_name: str, message: str):
        """HR 邀约面试或索要联系方式时触发高优先级警报与微信/飞书智能触达"""
        res = self.bot_manager.notify_interview_event(
            company=company,
            job_title=job_title,
            hr_name=hr_name,
            message=message
        )
        self._dispatch(res["title"], f"**公司**: {company}\n**岗位**: {job_title}\n**HR**: {hr_name}\n**最新消息**: {message}\n\n📋 **微信好友申请打招呼词**:\n> {res['wechat_greeting']}\n\n⚠️ **AI 已自动暂停该会话回复，请立即打开浏览器手动接管！**", alert_type="INTERVIEW")

    def send_safety_alert(self, company: str, job_title: str, hr_name: str, message: str, reason: str):
        """高危风险/涉诈诱导拦截警报 (严禁生成打招呼词，红牌警告)"""
        title = f"🚨 【高危涉诈/人身安全风险拦截】[{company}]"
        content = (
            f"**涉事企业**: {company}\n"
            f"**涉及岗位**: {job_title}\n"
            f"**HR/发布人**: {hr_name}\n"
            f"**拦截原因**: ❌ {reason}\n"
            f"**HR 原消息**: \"{message}\"\n\n"
            f"🛡️ **安全操作提示**:\n"
            f"1. 系统已**紧急就地熔断并阻断 AI 回复**，防止掉入套路陷阱！\n"
            f"2. **严禁**添加对方提供的第三方聊天软件（飞机/纸飞机/Telegram/外部App）！\n"
            f"3. **严禁**向对方支付任何押金、体检费、服装费或提供银行卡/微信跑分！\n"
            f"4. 建议直接在 BOSS 直聘上点击右上角【举报该职位/公司】。"
        )
        self._dispatch(title, content, alert_type="RISK_BLOCKED")

    def send_captcha_alert(self):
        """触发滑块验证码时的紧急警报"""
        title = "🚨 检测到招聘网站滑块验证码！"
        content = (
            "系统已自动熔断暂停所有自动化任务。\n"
            "请前往电脑浏览器窗口，手动拖动滑块完成验证。\n"
            "完成后在控制台按回车继续。"
        )
        self._dispatch(title, content, alert_type="CAPTCHA")

    def send_daily_summary(self, total_scanned: int, applied: int, high_match_list: list):
        """每日投递汇总报告"""
        title = "📊 今日求职 Agent 运行日报"
        content = (
            f"**今日扫描岗位**: {total_scanned} 个\n"
            f"**成功发起沟通**: {applied} 个\n"
            f"**重点推荐岗位**:\n"
        )
        for item in high_match_list[:5]:
            content += f"• [{item.get('company')}] {item.get('title')} ({item.get('score')}分) - {item.get('salary')}\n"
            
        self._dispatch(title, content, alert_type="SUMMARY")

    def _dispatch(self, title: str, markdown_content: str, alert_type: str = "INFO"):
        """分发消息至各渠道"""
        msg_str = f"\n[{alert_type}] {title}\n{markdown_content}\n"
        try:
            print(msg_str)
        except UnicodeEncodeError:
            # 在 Windows GBK 终端下安全回退输出
            clean_str = msg_str.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8")
            print(clean_str)
        
        # 1. 飞书 Webhook 交互卡片
        if self.feishu_webhook:
            try:
                card_payload = {
                    "msg_type": "interactive",
                    "card": {
                        "header": {
                            "title": {"tag": "plain_text", "content": title},
                            "template": "red" if alert_type in ["INTERVIEW", "CAPTCHA"] else "blue"
                        },
                        "elements": [
                            {
                                "tag": "markdown",
                                "content": markdown_content
                            }
                        ]
                    }
                }
                httpx.post(self.feishu_webhook, json=card_payload, timeout=5.0)
            except Exception as e:
                logger.error(f"Failed to send Feishu webhook: {e}")

        # 2. 微信 PushPlus 推送
        if self.pushplus_token:
            try:
                push_payload = {
                    "token": self.pushplus_token,
                    "title": title,
                    "content": markdown_content.replace("\n", "<br>"),
                    "template": "html"
                }
                httpx.post("http://www.pushplus.plus/send", json=push_payload, timeout=5.0)
            except Exception as e:
                logger.error(f"Failed to send PushPlus notification: {e}")

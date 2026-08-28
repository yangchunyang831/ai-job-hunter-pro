"""WeChat (WeCom/PushPlus) & Feishu Bot Notification and HR Greeting Dispatcher."""
import re
import json
import logging
import httpx
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class BotManager:
    """微信与飞书多通道智能推送与 HR 触达管理器"""
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = str(Path(__file__).resolve().parent.parent / "config" / "bot_config.yaml")
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return {}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading bot config: {e}")
            return {}

    def reload_config(self):
        self.config = self._load_config()

    def send_feishu_card(self, title: str, content: str, fields: Optional[List[Dict[str, str]]] = None) -> bool:
        """发送飞书富文本交互卡片消息"""
        feishu_cfg = self.config.get("feishu", {})
        if not feishu_cfg.get("enabled", False):
            return False

        webhook_url = feishu_cfg.get("webhook_url", "")
        if not webhook_url or "your_feishu" in webhook_url:
            logger.info("飞书 Webhook 未配置真实 Token，跳过实际网络请求。")
            return False

        elements = [{"tag": "markdown", "content": content}]
        if fields:
            field_list = []
            for f in fields:
                field_list.append({
                    "is_short": True,
                    "text": {"tag": "lark_md", "content": f"**{f.get('key')}**: {f.get('value')}"}
                })
            elements.append({"tag": "div", "fields": field_list})

        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": f"🎯 {title}"},
                    "template": "blue"
                },
                "elements": elements
            }
        }

        try:
            resp = httpx.post(webhook_url, json=payload, timeout=8.0)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send Feishu card: {e}")
            return False

    def send_wechat_message(self, title: str, content: str) -> bool:
        """发送企业微信 / 微信推送消息"""
        wechat_cfg = self.config.get("wechat", {})
        if not wechat_cfg.get("enabled", False):
            return False

        channel = wechat_cfg.get("channel", "wecom_webhook")
        
        # 1. 企业微信群机器人 Webhook
        if channel == "wecom_webhook":
            webhook_url = wechat_cfg.get("webhook_url", "")
            if not webhook_url or "your_wecom" in webhook_url:
                logger.info("企业微信 Webhook 未配置真实 Key，跳过实际网络请求。")
                return False

            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "content": f"### {title}\n{content}"
                }
            }
            try:
                resp = httpx.post(webhook_url, json=payload, timeout=8.0)
                return resp.status_code == 200
            except Exception as e:
                logger.error(f"Failed to send WeCom message: {e}")
                return False

        # 2. PushPlus (个人微信直接弹窗)
        elif channel == "pushplus":
            token = wechat_cfg.get("pushplus_token", "")
            if not token:
                return False
            payload = {
                "token": token,
                "title": title,
                "content": content,
                "template": "markdown"
            }
            try:
                resp = httpx.post("http://www.pushplus.plus/send", json=payload, timeout=8.0)
                return resp.status_code == 200
            except Exception as e:
                logger.error(f"Failed to send PushPlus message: {e}")
                return False

        return False

    def generate_hr_greeting(self, hr_contact: str, channel: str = "wechat") -> str:
        """根据渠道与 HR 联系方式自动生成复制即用的话术"""
        tpls = self.config.get("contact_greeting_templates", {})
        if channel == "wechat":
            return tpls.get("wechat_friend_request", "您好，我是BOSS直聘沟通的杨春，特来添加您的微信，已备好简历，期待与您交流！")
        elif channel == "feishu":
            return tpls.get("feishu_friend_request", "您好，我是应聘贵司岗位的杨春，特来添加您的飞书，已同步简历，请多关照！")
        return tpls.get("phone_sms_followup", "HR老师您好，我是BOSS直聘沟通的杨春，已将简历发送给您，祝工作顺利！")

    def notify_interview_event(self, company: str, job_title: str, hr_name: str, message: str) -> Dict[str, Any]:
        """全通道高亮广播面试邀约与联系方式事件"""
        title = f"🎉 收到面试邀约 / 联系方式请求 [{company}]"
        
        # 提取可能的手机号/微信号
        phone_match = re.findall(r"1[3-9]\d{9}", message)
        detected_phone = phone_match[0] if phone_match else None
        
        wechat_greeting = self.generate_hr_greeting(detected_phone or "", channel="wechat")
        
        content = (
            f"**公司**: {company}\n"
            f"**岗位**: {job_title}\n"
            f"**HR**: {hr_name}\n"
            f"**最新消息**: {message}\n\n"
            f"📋 **自动生成微信申请打招呼词 (可一键复制)**:\n"
            f"> {wechat_greeting}\n\n"
            f"⚠️ **AI 已自动暂停该会话回复，请立即打开微信/浏览器进行手动对接！**"
        )

        fields = [
            {"key": "公司", "value": company},
            {"key": "岗位", "value": job_title},
            {"key": "HR", "value": hr_name},
            {"key": "提取电话/微信", "value": detected_phone or "需人工查看"}
        ]

        # 广播到飞书与微信
        feishu_ok = self.send_feishu_card(title=title, content=content, fields=fields)
        wechat_ok = self.send_wechat_message(title=title, content=content)

        return {
            "title": title,
            "detected_phone": detected_phone,
            "wechat_greeting": wechat_greeting,
            "feishu_sent": feishu_ok,
            "wechat_sent": wechat_ok
        }

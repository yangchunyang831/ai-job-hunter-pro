"""
Enhanced WeChat (WeCom/PushPlus/ServerChan), Feishu & AstrBot Multi-Channel Notification Manager.
Supports direct personal account integration via AstrBot / OneBot / WeChat / Feishu.
"""
import re
import json
import logging
import httpx
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class BotManager:
    """微信、飞书与 AstrBot 个人账号多通道智能推送与 HR 触达管理器"""
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

    def send_astrbot_message(self, message: str, target_id: Optional[str] = None) -> bool:
        """通过 AstrBot 个人账号中枢（支持个人微信/QQ/飞书/TG）推送消息"""
        astr_cfg = self.config.get("astrbot", {})
        if not astr_cfg.get("enabled", False):
            return False

        api_url = astr_cfg.get("api_url", "").strip()
        if not api_url:
            return False

        token = astr_cfg.get("token", "").strip()
        msg_type = astr_cfg.get("message_type", "private")
        user_or_group_id = target_id or astr_cfg.get("target_id", "")

        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        # 兼容 AstrBot 原生 API 与 OneBot V11 标准
        payload = {
            "message_type": msg_type,
            "user_id": user_or_group_id,
            "group_id": user_or_group_id,
            "target_id": user_or_group_id,
            "message": message
        }

        try:
            resp = httpx.post(api_url, json=payload, headers=headers, timeout=8.0)
            return resp.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Failed to send AstrBot message: {e}")
            return False

    def send_feishu_card(self, title: str, content: str, fields: Optional[List[Dict[str, str]]] = None, template_color: str = "blue") -> bool:
        """发送飞书富文本交互卡片消息"""
        feishu_cfg = self.config.get("feishu", {})
        if not feishu_cfg.get("enabled", False):
            return False

        webhook_url = feishu_cfg.get("webhook_url", "").strip()
        if not webhook_url or "your_feishu" in webhook_url:
            logger.info("飞书 Webhook 未配置真实 URL，跳过实际网络请求。")
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
                    "template": template_color
                },
                "elements": elements
            }
        }

        try:
            resp = httpx.post(webhook_url, json=payload, timeout=8.0)
            if resp.status_code == 200:
                res_json = resp.json()
                return res_json.get("code") == 0 or res_json.get("StatusCode") == 0
            return False
        except Exception as e:
            logger.error(f"Failed to send Feishu card: {e}")
            return False

    def send_wechat_message(self, title: str, content: str) -> bool:
        """发送企业微信 / PushPlus / ServerChan 微信推送消息"""
        wechat_cfg = self.config.get("wechat", {})
        if not wechat_cfg.get("enabled", False):
            return False

        channel = wechat_cfg.get("channel", "wecom_webhook")
        
        # 1. 企业微信群机器人 Webhook
        if channel == "wecom_webhook":
            webhook_url = wechat_cfg.get("webhook_url", "").strip()
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
                if resp.status_code == 200:
                    return resp.json().get("errcode") == 0
                return False
            except Exception as e:
                logger.error(f"Failed to send WeCom message: {e}")
                return False

        # 2. PushPlus (个人微信直接弹窗)
        elif channel == "pushplus":
            token = wechat_cfg.get("pushplus_token", "").strip()
            if not token:
                logger.info("PushPlus Token 未配置，跳过发送。")
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

        # 3. ServerChan (微信方糖推送)
        elif channel == "serverchan":
            sendkey = wechat_cfg.get("serverchan_sendkey", "").strip()
            if not sendkey:
                return False
            payload = {
                "title": title,
                "desp": content
            }
            try:
                resp = httpx.post(f"https://sctapi.ftqq.com/{sendkey}.send", json=payload, timeout=8.0)
                return resp.status_code == 200
            except Exception as e:
                logger.error(f"Failed to send ServerChan message: {e}")
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

    def notify_resume_sent_event(self, hr_name: str, job_info: str) -> Dict[str, Any]:
        """广播简历送达事件至 AstrBot、飞书与微信"""
        title = f"📄 简历已正式送达 HR [{hr_name}]"
        content = (
            f"🎯 **【AI 求职猎头·投递通知】**\n\n"
            f"👤 **求职者**: 杨春 (区块链工程本科 / 英语客服专向)\n"
            f"💼 **对接 HR**: {hr_name}\n"
            f"🏢 **岗位信息**: {job_info}\n"
            f"✅ **投递状态**: 完整三步官方流程交付成功（在线简历已送达）\n"
            f"🤫 **后续策略**: AI 已自动进入静默守候，等待 HR 进一步消息通知！"
        )
        fields = [
            {"key": "HR", "value": hr_name},
            {"key": "岗位", "value": job_info},
            {"key": "交付方式", "value": "BOSS 官方在线简历"},
            {"key": "当前状态", "value": "等待 HR 审阅"}
        ]
        
        # 广播到 AstrBot 个人账号
        astr_ok = self.send_astrbot_message(message=content)
        # 广播到飞书
        feishu_ok = self.send_feishu_card(title=title, content=content, fields=fields, template_color="green")
        # 广播到微信
        wechat_ok = self.send_wechat_message(title=title, content=content)
        
        return {"astrbot_sent": astr_ok, "feishu_sent": feishu_ok, "wechat_sent": wechat_ok}

    def notify_interview_event(self, company: str, job_title: str, hr_name: str, message: str) -> Dict[str, Any]:
        """全通道高亮广播面试邀约与联系方式事件至 AstrBot、飞书与微信"""
        title = f"🎉 收到面试邀约 / 联系方式请求 [{company}]"
        phone_match = re.findall(r"1[3-9]\d{9}", message)
        detected_phone = phone_match[0] if phone_match else None
        wechat_greeting = self.generate_hr_greeting(detected_phone or "", channel="wechat")
        
        content = (
            f"🚨 **【AI 求职猎头·面试与联系方式极速预警】**\n\n"
            f"🏢 **公司**: {company}\n"
            f"💼 **岗位**: {job_title}\n"
            f"👤 **HR**: {hr_name}\n"
            f"💬 **最新消息**: {message}\n"
            f"📱 **提取电话/微信**: {detected_phone or '需人工查看'}\n\n"
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
        
        astr_ok = self.send_astrbot_message(message=content)
        feishu_ok = self.send_feishu_card(title=title, content=content, fields=fields, template_color="red")
        wechat_ok = self.send_wechat_message(title=title, content=content)
        
        return {
            "title": title,
            "detected_phone": detected_phone,
            "wechat_greeting": wechat_greeting,
            "astrbot_sent": astr_ok,
            "feishu_sent": feishu_ok,
            "wechat_sent": wechat_ok
        }

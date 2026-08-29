"""Finite State Machine (FSM) for multi-turn dialogue with HR and progressive inquiry dispatch with safety firewall."""
import json
import logging
from typing import Dict, Any, Optional, Tuple, List, Union
from openai import OpenAI
from src.schemas import ConversationState, HRIntent
from src.config_loader import ConfigManager
from src.notifier import NotificationManager
from src.resilient_client import ResilientAPIClient

logger = logging.getLogger(__name__)


class ConversationFSM:
    """多轮对话状态机、意图应答分发器与高危风控防火墙"""

    # 高危涉诈与人身安全诱导关键词
    HIGH_RISK_LURE_PATTERNS = [
        "飞机号", "telegram", "纸飞机", "下载我们专属app", "海外工作", "缅甸", "柬埔寨",
        "出境工作", "包机票签证", "带薪出国", "跑分", "刷流水", "转账测试", "提供银行卡",
        "交纳培训费", "押金", "入职体检指定收费医院", "服装费", "公关陪侍", "高额拍摄费"
    ]

    def __init__(
        self,
        config_manager: ConfigManager,
        notifier: NotificationManager,
        client: Optional[Union[OpenAI, ResilientAPIClient]] = None,
        model: str = "deepseek-chat"
    ):
        self.config_manager = config_manager
        self.notifier = notifier
        self.client = client
        self.model = model

    def check_high_risk_hr_message(self, hr_message: str) -> Tuple[bool, Optional[str]]:
        """检查 HR 发送的消息中是否暗含高危诱导/诈骗/违法违规内容"""
        msg_lower = hr_message.lower()
        for kw in self.HIGH_RISK_LURE_PATTERNS:
            if kw in msg_lower:
                return True, f"命中高危敏感词/套路诱导: [{kw}]"
        return False, None

    def classify_hr_intent(self, hr_message: str) -> HRIntent:
        """分类 HR 消息意图"""
        # 1. 规则快速命中
        msg_lower = hr_message.lower()
        if any(kw in msg_lower for kw in ["发一份简历", "发个简历", "发下简历", "发简历", "附件简历", "看看简历", "投递简历"]):
            return HRIntent.ASK_RESUME

        if any(kw in msg_lower for kw in ["面试", "聊聊吗", "方便电话", "腾讯会议", "来公司", "现场面", "视频面", "几点有空", "约个时间"]):
            return HRIntent.INVITE_INTERVIEW

        if any(kw in msg_lower for kw in ["微信号", "加个v", "加微信", "手机号", "电话多少", "留个联系方式", "微信是"]):
            return HRIntent.ASK_CONTACT

        if any(kw in msg_lower for kw in ["离职", "什么时候到岗", "目前薪资", "期望薪资", "在职还是", "住哪里", "到岗时间"]):
            return HRIntent.ASK_BASIC_INFO

        if any(kw in msg_lower for kw in ["不合适", "已招满", "感谢关注", "不匹配", "暂不考虑", "遗憾"]):
            return HRIntent.REJECTION

        # 2. LLM / ResilientClient 智能分类兜底
        if self.client:
            prompt = (
                "请将以下招聘 HR 发送的消息分类为以下枚举之一："
                "[ASK_RESUME, ASK_BASIC_INFO, TECHNICAL_DISCUSSION, INVITE_INTERVIEW, ASK_CONTACT, REJECTION, UNKNOWN]\n"
                f"HR 消息内容: {hr_message}\n"
                "仅输出枚举值本身，不要有其他解释。"
            )
            try:
                if isinstance(self.client, ResilientAPIClient):
                    res_text, _ = self.client.create_chat_completion(
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.0
                    )
                    intent_str = (res_text or "").strip().upper()
                else:
                    resp = self.client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.0
                    )
                    intent_str = resp.choices[0].message.content.strip().upper()

                if hasattr(HRIntent, intent_str):
                    return getattr(HRIntent, intent_str)
            except Exception as e:
                logger.error(f"Intent classification failed: {e}")

        return HRIntent.TECHNICAL_DISCUSSION

    def generate_next_response(
        self,
        company_name: str,
        job_title: str,
        hr_name: str,
        hr_message: str,
        conversation_history: List[Dict[str, str]],
        unasked_inquiries: List[str]
    ) -> Tuple[Optional[str], ConversationState, bool]:
        """
        处理 HR 消息并生成下一轮回复
        返回: (response_text, new_state, requires_human_takeover)
        """
        # 0. 优先执行：高危风险与涉诈防线审查 (最高优先级防御)
        is_risky, risk_reason = self.check_high_risk_hr_message(hr_message)
        if is_risky:
            logger.warning(f"🚨 High-risk HR message detected: {risk_reason} from {company_name} ({hr_name})")
            self.notifier.send_safety_alert(company_name, job_title, hr_name, hr_message, risk_reason)
            return None, ConversationState.WAITING_HUMAN, True

        intent = self.classify_hr_intent(hr_message)
        profile = self.config_manager.profile_config

        # 1. 触发人工接管状态 (约面试 / 要联系方式)
        if intent in [HRIntent.INVITE_INTERVIEW, HRIntent.ASK_CONTACT]:
            self.notifier.send_interview_alert(company_name, job_title, hr_name, hr_message)
            return None, ConversationState.WAITING_HUMAN, True

        # 2. 索要简历意图
        if intent == HRIntent.ASK_RESUME:
            reply = "好的，附件简历已发送，请您查收！"
            if unasked_inquiries:
                next_q = unasked_inquiries.pop(0)
                reply += f" 另外想向您请教一下，{next_q}"
            return reply, ConversationState.RESUME_SENT, False

        # 3. 询问基础信息 (到岗时间/离职状态/期望薪资)
        if intent == HRIntent.ASK_BASIC_INFO:
            basics = profile.get("basics", {})
            status = basics.get("current_status", "目前离职，可随时到岗")
            salary_exp = profile.get("salary_expectations", {})
            target_salary = f"{salary_exp.get('min_monthly_base_k', 3.5)}-{salary_exp.get('target_monthly_base_k', 5.5)}K"
            
            reply = f"您好，我常住湖南洪江市，{status}，期望薪资在 {target_salary} 左右。"
            if unasked_inquiries:
                next_q = unasked_inquiries.pop(0)
                reply += f" 另外想向您了解一下，{next_q}"
            return reply, ConversationState.INQUIRY_IN_PROGRESS, False

        # 4. 委婉拒绝意图
        if intent == HRIntent.REJECTION:
            return "好的，非常感谢您的回复与关注，祝贵司早日招到合适的人才！", ConversationState.CLOSED, False

        # 5. 业务交流与日常沟通 (结合事实库由 ResilientClient / LLM 生成)
        next_inquiry_part = ""
        if unasked_inquiries:
            next_inquiry_part = f"在回答完 HR 的问题后，顺带自然、委婉地向 HR 询问这个问题：'{unasked_inquiries.pop(0)}'"

        system_prompt = (
            "你是一个正在与 HR 沟通的求职者杨春（湖南信息学院区块链工程本科，持C1驾照，熟悉办公自动化与IT运维）。\n"
            "请根据候选人真实背景客观、谦逊、真诚地回答，字数控制在 100 字以内，严禁编造虚假经历。\n"
            f"{next_inquiry_part}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            *conversation_history,
            {"role": "user", "content": hr_message}
        ]

        if isinstance(self.client, ResilientAPIClient):
            reply_text, _ = self.client.create_chat_completion(
                messages=messages,
                temperature=0.4
            )
            return reply_text or "感谢您的回复！请问咱们后续的沟通流程大概是怎样的呢？", ConversationState.INQUIRY_IN_PROGRESS, False

        elif isinstance(self.client, OpenAI):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.4
                )
                return resp.choices[0].message.content.strip(), ConversationState.INQUIRY_IN_PROGRESS, False
            except Exception as e:
                logger.error(f"Generate response failed: {e}")

        return "感谢您的回复！请问咱们后续的沟通流程大概是怎样的呢？", ConversationState.INQUIRY_IN_PROGRESS, False

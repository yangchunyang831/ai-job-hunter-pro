"""Finite State Machine (FSM) for multi-turn dialogue with HR and progressive inquiry dispatch."""
import json
import logging
from typing import Dict, Any, Optional, Tuple, List
from openai import OpenAI
from src.schemas import ConversationState, HRIntent
from src.config_loader import ConfigManager
from src.notifier import NotificationManager

logger = logging.getLogger(__name__)


class ConversationFSM:
    """多轮对话状态机与意图应答分发器"""
    def __init__(self, config_manager: ConfigManager, notifier: NotificationManager, client: Optional[OpenAI] = None, model: str = "deepseek-chat"):
        self.config_manager = config_manager
        self.notifier = notifier
        self.client = client
        self.model = model

    def classify_hr_intent(self, hr_message: str) -> HRIntent:
        """分类 HR 消息意图"""
        # 1. 规则快速命中
        msg_lower = hr_message.lower()
        if any(kw in msg_lower for kw in ["发一份简历", "发个简历", "发下简历", "发简历", "附件简历", "看看简历"]):
            return HRIntent.ASK_RESUME

        if any(kw in msg_lower for kw in ["面试", "聊聊吗", "方便电话", "腾讯会议", "来公司", "现场面", "视频面", "几点有空"]):
            return HRIntent.INVITE_INTERVIEW

        if any(kw in msg_lower for kw in ["微信号", "加个v", "加微信", "手机号", "电话多少", "留个联系方式"]):
            return HRIntent.ASK_CONTACT

        if any(kw in msg_lower for kw in ["离职", "什么时候到岗", "目前薪资", "期望薪资", "在职还是"]):
            return HRIntent.ASK_BASIC_INFO

        if any(kw in msg_lower for kw in ["不合适", "已招满", "感谢关注", "不匹配", "暂不考虑"]):
            return HRIntent.REJECTION

        # 2. LLM 智能分类兜底
        if self.client:
            prompt = (
                "请将以下招聘 HR 发送的消息分类为以下枚举之一："
                "[ASK_RESUME, ASK_BASIC_INFO, TECHNICAL_DISCUSSION, INVITE_INTERVIEW, ASK_CONTACT, REJECTION, UNKNOWN]\n"
                f"HR 消息内容: {hr_message}\n"
                "仅输出枚举值本身，不要有其他解释。"
            )
            try:
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
        intent = self.classify_hr_intent(hr_message)
        profile = self.config_manager.profile_config

        # 1. 触发人工接管状态 (约面试 / 要联系方式)
        if intent in [HRIntent.INVITE_INTERVIEW, HRIntent.ASK_CONTACT]:
            self.notifier.send_interview_alert(company_name, job_title, hr_name, hr_message)
            return None, ConversationState.WAITING_HUMAN, True

        # 2. 索要简历意图
        if intent == HRIntent.ASK_RESUME:
            reply = "好的，附件简历已发送，请您查收！"
            # 如果还有未提问的自定义问题，顺带提 1 个
            if unasked_inquiries:
                next_q = unasked_inquiries.pop(0)
                reply += f" 另外想向您请教一下，{next_q}"
            return reply, ConversationState.RESUME_SENT, False

        # 3. 询问基础信息 (到岗时间/离职状态/期望薪资)
        if intent == HRIntent.ASK_BASIC_INFO:
            basics = profile.get("basics", {})
            status = basics.get("current_status", "目前离职，可随时到岗")
            salary_exp = profile.get("salary_expectations", {})
            target_salary = f"{salary_exp.get('min_monthly_base_k')}-{salary_exp.get('target_monthly_base_k')}K"
            
            reply = f"您好，我{status}，期望薪资在 {target_salary} 左右。"
            if unasked_inquiries:
                next_q = unasked_inquiries.pop(0)
                reply += f" 另外想向您了解一下，{next_q}"
            return reply, ConversationState.INQUIRY_IN_PROGRESS, False

        # 4. 技术与业务讨论 (结合事实库由 LLM 生成回复 + 顺带抛出 1 个追问)
        if self.client:
            next_inquiry_part = ""
            if unasked_inquiries:
                next_inquiry_part = f"在回答完 HR 的问题后，顺带自然、委婉地向 HR 询问这个问题：'{unasked_inquiries.pop(0)}'"

            system_prompt = (
                "你是一个正在与 HR/面试官沟通的候选人。请根据【候选人事实知识库】礼貌、专业、客观地回答对方的问题。\n"
                "【严格原则】：严禁编造任何知识库中没有的内容。字数控制在 100 字以内，语气谦逊真诚。\n"
                f"{next_inquiry_part}"
            )
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        *conversation_history,
                        {"role": "user", "content": hr_message}
                    ],
                    temperature=0.4
                )
                return resp.choices[0].message.content.strip(), ConversationState.INQUIRY_IN_PROGRESS, False
            except Exception as e:
                logger.error(f"Generate response failed: {e}")

        return "感谢您的回复！请问咱们后续的沟通流程大概是怎样的呢？", ConversationState.INQUIRY_IN_PROGRESS, False

"""Pydantic data schemas for Job, Evaluation, Spatial Tiers, and Conversation States."""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class GeoTierLevel(str, Enum):
    TIER1_LOCAL = "tier1_local"           # 10km 本地极限通勤圈
    TIER2_ADJACENT = "tier2_adjacent"     # 邻近核心地级市
    TIER3_PROVINCE = "tier3_province"     # 省内中心城市
    TIER4_REMOTE_OR_NATIONAL = "tier4_remote_or_national" # 远程/全国优质


class ConversationState(str, Enum):
    INIT = "INIT"                         # 初始匹配
    GREETED = "GREETED"                   # 已发送打招呼语
    HR_REPLIED = "HR_REPLIED"             # HR 已回复
    INQUIRY_IN_PROGRESS = "INQUIRY_IN_PROGRESS" # 正在逐步摸底与追问
    RESUME_SENT = "RESUME_SENT"           # 已发送附件简历
    WAITING_HUMAN = "WAITING_HUMAN"       # 遇到约面/要微信/异常，等待人工接管
    CLOSED = "CLOSED"                     # 会话结束/淘汰


class HRIntent(str, Enum):
    ASK_RESUME = "ASK_RESUME"             # 索要简历
    ASK_BASIC_INFO = "ASK_BASIC_INFO"     # 询问离职状态/到岗时间/目前薪资
    TECHNICAL_DISCUSSION = "TECHNICAL_DISCUSSION" # 技术/业务问题交流
    INVITE_INTERVIEW = "INVITE_INTERVIEW" # 邀约面试 (电话/视频/现场)
    ASK_CONTACT = "ASK_CONTACT"           # 索要电话/微信
    REJECTION = "REJECTION"               # 婉拒/已招满
    UNKNOWN = "UNKNOWN"                   # 其他闲聊/未知


class RawJobCard(BaseModel):
    """从页面或接口提取的原始岗位卡片数据"""
    job_id: str
    job_title: str
    company_name: str
    salary_raw: str
    city: str
    district: Optional[str] = None
    subway_station: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    hr_name: str = ""
    hr_title: str = ""
    hr_active_status: str = "刚刚活跃"
    jd_text: str = ""
    company_scale: Optional[str] = None
    is_remote: bool = False


class JobEvaluationResult(BaseModel):
    """LLM 结构化打分与决策结果"""
    score: int = Field(..., ge=0, le=100, description="综合匹配度得分 0-100")
    passed: bool = Field(..., description="是否通过阈值进入投递队列")
    tier_level: GeoTierLevel
    distance_km: Optional[float] = None
    match_highlights: List[str] = Field(default_factory=list, description="用于生成话术的核心亮点")
    risk_factors: List[str] = Field(default_factory=list, description="潜在风险与不匹配点")
    custom_greeting: Optional[str] = Field(None, description="生成的个性化高回复率打招呼语")
    rejection_reason: Optional[str] = None


class InquirySlot(BaseModel):
    """单条追问或摸底槽位"""
    key: str
    question_text: str
    status: str = "PENDING"  # PENDING, ASKED, ANSWERED, SKIPPED
    answer_extracted: Optional[str] = None

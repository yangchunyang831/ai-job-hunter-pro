"""LLM-based job screening, scoring, and tailored greeting generation."""
import os
import json
import re
import logging
from typing import Dict, Any, Optional, Tuple
from openai import OpenAI
from src.schemas import JobEvaluationResult, GeoTierLevel, RawJobCard
from src.config_loader import ConfigManager

logger = logging.getLogger(__name__)


class ScoringEngine:
    """岗位多维筛选与 LLM 打分引擎"""
    def __init__(self, config_manager: ConfigManager, api_key: Optional[str] = None, base_url: Optional[str] = None, model: str = "deepseek-chat"):
        self.config_manager = config_manager
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL") or "https://api.deepseek.com/v1"
        self.model = model
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = None
            logger.warning("No LLM API Key provided; ScoringEngine will run in rule-only or mock mode.")

    SAFETY_RISK_KEYWORDS = [
        "出境", "出国", "海外高薪", "柬埔寨", "缅甸", "老挝", "菲律宾", "迪拜客服", "包机票签证",
        "兼职刷单", "挂机", "资金盘", "跑分", "租借微信", "租借银行卡", "微信解封", "兼职模特高额拍摄费",
        "入职需交押金", "先培训后付款", "培训费自理", "自费考证", "夜总会", "商务伴游", "公关佳丽",
        "陪酒", "高利贷", "催收部", "博彩", "棋牌推广"
    ]

    def _parse_salary_to_k(self, salary_raw: str) -> Tuple[Optional[float], Optional[float]]:
        """解析多种格式薪资为标准千元 (K/月)"""
        if not salary_raw or "面议" in salary_raw:
            return None, None
        
        # 1. 常见 15-30K, 3-5K
        match_k = re.findall(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*K", salary_raw, re.IGNORECASE)
        if match_k:
            return float(match_k[0][0]), float(match_k[0][1])

        # 2. 3000-5000元/月, 3000-5000
        match_yuan = re.findall(r"(\d{4,6})\s*-\s*(\d{4,6})", salary_raw)
        if match_yuan:
            return round(float(match_yuan[0][0]) / 1000.0, 1), round(float(match_yuan[0][1]) / 1000.0, 1)

        # 3. 3-5千/月
        match_qian = re.findall(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*千", salary_raw)
        if match_qian:
            return float(match_qian[0][0]), float(match_qian[0][1])

        return None, None

    def pre_filter_hard_rules(self, job: RawJobCard) -> Tuple[bool, Optional[str]]:
        """第一层：人身安全、合规反诈、硬性规则与黑名单零 Token 过滤"""
        blacklist = self.config_manager.blacklist_config
        jd = (job.jd_text or "") + " " + (job.job_title or "")
        company = job.company_name or ""

        # 0. 🛡️ 最高优先级：人身安全与反诈灰产一票否决
        for safe_kw in self.SAFETY_RISK_KEYWORDS:
            if safe_kw in jd or safe_kw in company:
                return False, f"🛑 触发人身安全/反诈高危风控拦截: 包含【{safe_kw}】"

        # 1. 外包公司名称过滤
        for ob in blacklist.get("outsourcing_companies", []):
            if ob in company:
                return False, f"命中外包企业黑名单: {ob}"

        for custom_comp in blacklist.get("custom_company_blacklist", []):
            if custom_comp in company:
                return False, f"命中自定义企业黑名单: {custom_comp}"

        # 2. JD 关键词过滤
        for kw in blacklist.get("jd_forbidden_keywords", []):
            if kw in jd:
                return False, f"JD/标题包含违禁词: {kw}"

        # 3. 薪资套路分析与底线核验
        min_k, max_k = self._parse_salary_to_k(job.salary_raw)
        if min_k is not None and max_k is not None:
            ratio_limit = blacklist.get("salary_anomaly_rules", {}).get("max_ratio_allowed", 2.5)
            if min_k > 0 and (max_k / min_k) > ratio_limit:
                return False, f"薪资跨度异常 ({job.salary_raw})，判定为画饼/纯提成岗"

            # 最低薪资底线
            min_acceptable = float(self.config_manager.profile_config.get("salary_expectations", {}).get("min_monthly_base_k", 3.0))
            if max_k < min_acceptable:
                return False, f"薪资上限 {max_k}K 低于求职者底线 {min_acceptable}K"

        # 4. HR 活跃度
        inactive_keywords = ["本周活跃", "近1月活跃", "半年前活跃"]
        if any(ik in job.hr_active_status for ik in inactive_keywords):
            return False, f"HR 不活跃: {job.hr_active_status}"

        return True, None

    def evaluate_job_with_llm(self, job: RawJobCard) -> JobEvaluationResult:
        """第三层：结合多城市地理层级与 LLM 深度语义打分"""
        # 1. 硬规则预过滤
        passed_pre, reject_reason = self.pre_filter_hard_rules(job)
        
        # 2. 地理层级判定
        tier, dist, tier_meta = self.config_manager.match_city_tier(
            city_name=job.city,
            district=job.district,
            target_lat=job.latitude,
            target_lon=job.longitude,
            is_remote=job.is_remote
        )

        # 检查该地理层级是否被用户勾选启用
        enabled_tiers = self.config_manager.cities_config.get("enabled_tiers", ["tier1_local", "tier2_adjacent", "tier3_province", "tier4_remote_or_national"])
        if tier.value not in enabled_tiers:
            return JobEvaluationResult(
                score=0,
                passed=False,
                tier_level=tier,
                distance_km=dist,
                rejection_reason=f"岗位所在区域 [{tier.value}] 未在用户启用的筛选层级中"
            )

        if not passed_pre:
            return JobEvaluationResult(
                score=0,
                passed=False,
                tier_level=tier,
                distance_km=dist,
                rejection_reason=reject_reason
            )

        # 3. 如果没有 API Key，退化为基于规则打分
        if not self.client:
            return JobEvaluationResult(
                score=82,
                passed=True,
                tier_level=tier,
                distance_km=dist,
                match_highlights=["教育背景与综合素养契合", "地理通勤圈与意向相符"],
                custom_greeting=f"您好！关注到咱们【{job.company_name}】正在招聘【{job.job_title}】，我的个人背景与任职要求契合度高，学习与执行力强，希望能与您进一步沟通交流！"
            )

        # 4. 构造 LLM 打分 Prompt
        profile = self.config_manager.profile_config
        system_prompt = (
            "你是一个严谨、务实、懂职场的智能求职顾问。请根据【候选人简历画像】和【目标岗位JD】评估匹配度 (0-100分)。\n"
            "【评估核心原则】:\n"
            "1. 严禁人身安全隐患与非法违规（若发现灰产、涉诈、出境、套路收费，直接判 0 分淘汰）。\n"
            "2. 候选人接受广谱合法岗位（包括计算机相关、行政、文职、运营、技术支持、商务接待/C1驾驶、仓储物流等各类合法工作）。\n"
            "3. 针对非技术类岗位，打招呼语必须真诚自然，突出本科素养、学习力与严谨态度，严禁在文职/行政岗位上生搬硬套不相关的深奥技术名词。\n"
            "输出必须为合法的 JSON 格式：score (int), passed (bool), match_highlights (list), risk_factors (list), custom_greeting (str), reason (str)."
        )

        user_content = f"""
【候选人画像】:
- 目标职位: {profile.get('basics', {}).get('target_roles')}
- 工作年限: {profile.get('basics', {}).get('years_of_experience')}年
- 核心技术栈: {json.dumps(profile.get('skills', {}), ensure_ascii=False)}
- 亮点项目: {json.dumps(profile.get('highlight_projects', []), ensure_ascii=False)}

【目标岗位 JD】:
- 职位名称: {job.job_title}
- 公司名称: {job.company_name}
- 薪资: {job.salary_raw}
- 距离/地理层级: {tier.value} ({dist} km)
- JD 详情:
{job.jd_text}
"""
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            raw_json = json.loads(resp.choices[0].message.content)
            
            score = int(raw_json.get("score", 0))
            min_score_required = tier_meta.get("min_score", 80)
            passed = score >= min_score_required

            return JobEvaluationResult(
                score=score,
                passed=passed,
                tier_level=tier,
                distance_km=dist,
                match_highlights=raw_json.get("match_highlights", []),
                risk_factors=raw_json.get("risk_factors", []),
                custom_greeting=raw_json.get("custom_greeting"),
                rejection_reason=raw_json.get("reason") if not passed else None
            )
        except Exception as e:
            logger.error(f"LLM evaluation failed: {e}")
            return JobEvaluationResult(
                score=50,
                passed=False,
                tier_level=tier,
                distance_km=dist,
                rejection_reason=f"LLM 评分异常: {str(e)}"
            )

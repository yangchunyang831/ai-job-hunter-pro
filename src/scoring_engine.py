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

    def pre_filter_hard_rules(self, job: RawJobCard) -> Tuple[bool, Optional[str]]:
        """第一层：硬性规则与黑名单零 Token 过滤"""
        blacklist = self.config_manager.blacklist_config
        
        # 1. 外包公司名称过滤
        company = job.company_name
        for ob in blacklist.get("outsourcing_companies", []):
            if ob in company:
                return False, f"命中外包企业黑名单: {ob}"

        for custom_comp in blacklist.get("custom_company_blacklist", []):
            if custom_comp in company:
                return False, f"命中自定义企业黑名单: {custom_comp}"

        # 2. JD 关键词过滤
        jd = job.jd_text
        for kw in blacklist.get("jd_forbidden_keywords", []):
            if kw in jd or kw in job.job_title:
                return False, f"JD/标题包含违禁词: {kw}"

        # 3. 薪资套路分析
        # 示例: 15-30K, 4-25K
        salary_match = re.findall(r"(\d+)-(\d+)K", job.salary_raw, re.IGNORECASE)
        if salary_match:
            min_k, max_k = int(salary_match[0][0]), int(salary_match[0][1])
            ratio_limit = blacklist.get("salary_anomaly_rules", {}).get("max_ratio_allowed", 2.3)
            if min_k > 0 and (max_k / min_k) > ratio_limit:
                return False, f"薪资跨度异常 ({job.salary_raw})，判定为画饼/纯提成岗"

            # 最低薪资底线
            min_acceptable = self.config_manager.profile_config.get("salary_expectations", {}).get("min_monthly_base_k", 20)
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
                score=80,
                passed=True,
                tier_level=tier,
                distance_km=dist,
                match_highlights=["具备核心技术栈匹配经历"],
                custom_greeting=f"您好！关注到咱们【{job.company_name}】的【{job.job_title}】岗位，我的技术背景与该方向高度吻合，期待与您进一步沟通！"
            )

        # 4. 构造 LLM 打分 Prompt
        profile = self.config_manager.profile_config
        system_prompt = (
            "你是一个资深的技术求职顾问。请根据【候选人简历画像】和【岗位JD】，对该岗位的匹配度进行严谨打分 (0-100)，"
            "并提取 1-2 个具体契合点生成 100 字以内的礼貌、专业、突出个人项目产出的定制打招呼语。\n"
            "必须输出合法的 JSON 格式，字段包含：score (int), passed (bool), match_highlights (list of str), risk_factors (list of str), custom_greeting (str), reason (str)."
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

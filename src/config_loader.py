"""Configuration loader for YAML configs with validation and helpers."""
import os
import math
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from src.schemas import GeoTierLevel


class ConfigManager:
    """全局配置管理器"""
    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            self.config_dir = Path(__file__).resolve().parent.parent / "config"
        else:
            self.config_dir = Path(config_dir)
            
        self.cities_config = self._load_yaml("cities.yaml")
        self.profile_config = self._load_yaml("candidate_profile.yaml")
        self.inquiry_config = self._load_yaml("inquiry_templates.yaml")
        self.blacklist_config = self._load_yaml("blacklist.yaml")

    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        filepath = self.config_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """根据两点经纬度计算球面直线距离 (单位: km)"""
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * c, 2)

    def match_city_tier(self, city_name: str, target_lat: Optional[float], target_lon: Optional[float], is_remote: bool = False) -> Tuple[GeoTierLevel, float, Dict[str, Any]]:
        """根据城市、坐标与远程标记，计算所属的地理辐射层级与策略参数"""
        if is_remote:
            return GeoTierLevel.TIER4_REMOTE_OR_NATIONAL, 0.0, {
                "min_score": 88,
                "priority_bonus": 20,
                "desc": "全国远程专属通道"
            }

        # 查找配置中的城市
        for c_key, c_val in self.cities_config.get("cities", {}).items():
            if c_val.get("city_name") in city_name or city_name in c_val.get("city_name", ""):
                anchor = c_val.get("anchor", {})
                anchor_lat = anchor.get("latitude")
                anchor_lon = anchor.get("longitude")
                
                dist = 0.0
                if target_lat and target_lon and anchor_lat and anchor_lon:
                    dist = self.calculate_distance(anchor_lat, anchor_lon, target_lat, target_lon)

                tiers = c_val.get("tiers", {})
                t1 = tiers.get("tier1_local_commute", {})
                if dist > 0 and dist <= t1.get("max_distance_km", 10.0):
                    return GeoTierLevel.TIER1_LOCAL, dist, {
                        "min_score": t1.get("min_score_required", 75),
                        "priority_bonus": t1.get("priority_bonus", 15),
                        "salary_ratio": t1.get("salary_adjustment_ratio", 0.9)
                    }

                t2 = tiers.get("tier2_adjacent_metro", {})
                return GeoTierLevel.TIER2_ADJACENT, dist, {
                    "min_score": t2.get("min_score_required", 80),
                    "priority_bonus": t2.get("priority_bonus", 5),
                    "salary_ratio": t2.get("salary_adjustment_ratio", 1.0)
                }

        # 默认为 Tier 4
        return GeoTierLevel.TIER4_REMOTE_OR_NATIONAL, 999.0, {
            "min_score": 90,
            "priority_bonus": -5,
            "salary_ratio": 1.25
        }

    def get_custom_inquiries_for_job(self, job_title: str, company_name: str, jd_text: str) -> List[str]:
        """组合基础摸底、职位类别模板与单岗位覆写，生成该岗位的待追问问题列表"""
        questions = []

        # 1. 基础摸底必查项
        baseline = self.inquiry_config.get("baseline_inquiries", {})
        if baseline.get("enabled", True):
            for item in baseline.get("items", {}).values():
                questions.append(item.get("question_prompt"))

        # 2. 单岗位/公司级覆写
        for override in self.inquiry_config.get("job_specific_inquiries", []):
            comp_kw = override.get("company_keyword")
            title_kw = override.get("job_title_keyword")
            if (comp_kw and comp_kw in company_name) or (title_kw and title_kw in job_title):
                questions.extend(override.get("custom_questions", []))

        # 3. 职位类别级匹配
        for cat in self.inquiry_config.get("category_inquiry_templates", {}).values():
            keywords = cat.get("matching_keywords", [])
            if any(kw.lower() in (job_title + jd_text).lower() for kw in keywords):
                for q in cat.get("questions", []):
                    questions.append(q.get("prompt"))

        return questions

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

    def match_city_tier(self, city_name: str, target_lat: Optional[float] = None, target_lon: Optional[float] = None, district: Optional[str] = None, is_remote: bool = False) -> Tuple[GeoTierLevel, float, Dict[str, Any]]:
        """
        根据城市、行政区、坐标与远程标记，精准计算所属的 4 级空间地理辐射层级与差异化策略
        """
        # 兼容若第二个参数传了字符串 district
        if isinstance(target_lat, str) and district is None:
            district = target_lat
            target_lat = None

        tiers_cfg = self.cities_config.get("tiers_config", {})
        user_res = self.cities_config.get("user_residence", {})

        # 检查是否命中远程/Remote 岗位
        if is_remote:
            t4_cfg = tiers_cfg.get("tier4_remote_or_national", {})
            return GeoTierLevel.TIER4_REMOTE_OR_NATIONAL, 0.0, {
                "min_score": t4_cfg.get("min_score", 88),
                "priority_bonus": t4_cfg.get("remote_job_bonus", 20),
                "desc": "全国远程专属通道 (+20分特权加分)"
            }

        home_city = user_res.get("city", "杭州")
        home_district = user_res.get("district", "余杭区")
        home_province = user_res.get("province", "浙江")
        home_lat = user_res.get("latitude", 30.2796)
        home_lon = user_res.get("longitude", 120.0253)

        # 1. 同城判定 (Tier 1 核心通勤圈 vs Tier 2 同城外围)
        if home_city and (home_city in city_name or city_name in home_city):
            dist = 0.0
            if target_lat and target_lon and home_lat and home_lon:
                dist = self.calculate_distance(home_lat, home_lon, target_lat, target_lon)

            t1 = tiers_cfg.get("tier1_local", {})
            max_dist = t1.get("max_distance_km", 10.0)
            is_same_district = bool(district and isinstance(district, str) and home_district and (district in home_district or home_district in district))

            if (dist > 0 and dist <= max_dist) or (dist == 0.0 and is_same_district):
                return GeoTierLevel.TIER1_LOCAL, (dist if dist > 0 else 4.5), {
                    "min_score": t1.get("min_score", 75),
                    "priority_bonus": t1.get("priority_bonus", 15),
                    "salary_ratio": t1.get("salary_ratio", 0.90),
                    "desc": "Tier 1: 本地神仙通勤圈"
                }

            t2 = tiers_cfg.get("tier2_adjacent", {})
            return GeoTierLevel.TIER2_ADJACENT, (dist if dist > 0 else 22.0), {
                "min_score": t2.get("min_score", 80),
                "priority_bonus": t2.get("priority_bonus", 5),
                "salary_ratio": t2.get("salary_ratio", 1.00),
                "desc": "Tier 2: 同城扩展圈"
            }

        # 2. 邻近 1 小时地级市判定 (Tier 2)
        t2 = tiers_cfg.get("tier2_adjacent", {})
        adjacent_cities = t2.get("adjacent_cities", ["绍兴", "嘉兴", "湖州", "宁波"])
        if any(ac in city_name for ac in adjacent_cities):
            return GeoTierLevel.TIER2_ADJACENT, 45.0, {
                "min_score": t2.get("min_score", 80),
                "priority_bonus": t2.get("priority_bonus", 5),
                "salary_ratio": t2.get("salary_ratio", 1.00),
                "desc": "Tier 2: 邻近核心地级市"
            }

        # 3. 同省内其他中心城市 (Tier 3)
        if home_province and (home_province in city_name or city_name in home_province):
            t3 = tiers_cfg.get("tier3_province", {})
            return GeoTierLevel.TIER3_PROVINCE, 120.0, {
                "min_score": t3.get("min_score", 85),
                "priority_bonus": t3.get("priority_bonus", 0),
                "salary_ratio": t3.get("salary_ratio", 1.15),
                "desc": "Tier 3: 省内其他中心城市"
            }

        # 4. 跨省全国优质机会 / 远程 (Tier 4)
        t4 = tiers_cfg.get("tier4_remote_or_national", {})
        return GeoTierLevel.TIER4_REMOTE_OR_NATIONAL, 999.0, {
            "min_score": t4.get("min_score", 88),
            "priority_bonus": 0,
            "salary_ratio": t4.get("salary_ratio", 1.30),
            "desc": "Tier 4: 全国一线重点/远程"
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

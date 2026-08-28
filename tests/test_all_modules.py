"""Automated Unit & Integration Test Suite for AI Job Hunting Agent."""
import os
import sys
import unittest
import tempfile
from pathlib import Path

# 添加项目根目录到 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.schemas import GeoTierLevel, RawJobCard, ConversationState, HRIntent
from src.config_loader import ConfigManager
from src.db_storage import DatabaseManager
from src.scoring_engine import ScoringEngine
from src.conversation_fsm import ConversationFSM
from src.notifier import NotificationManager


class TestConfigAndGeo(unittest.TestCase):
    """测试配置加载与地理空间距离计算"""
    def setUp(self):
        self.cfg = ConfigManager()
        self.cfg.cities_config["user_residence"] = {
            "city": "杭州",
            "district": "余杭区",
            "address": "杭州未来科技城",
            "latitude": 30.2796,
            "longitude": 120.0253,
            "province": "浙江"
        }
        self.cfg.cities_config["enabled_tiers"] = ["tier1_local", "tier2_adjacent", "tier3_province", "tier4_remote_or_national"]
        if "tier1_local" not in self.cfg.cities_config.get("tiers_config", {}):
            self.cfg.cities_config["tiers_config"] = {}
        self.cfg.cities_config["tiers_config"]["tier1_local"] = {
            "max_distance_km": 10.0,
            "min_score": 75,
            "salary_ratio": 0.90,
            "priority_bonus": 15
        }
        self.cfg.cities_config["tiers_config"]["tier2_adjacent"] = {
            "adjacent_cities": ["绍兴", "嘉兴", "湖州", "宁波"],
            "min_score": 80,
            "salary_ratio": 1.00,
            "priority_bonus": 5
        }

    def test_config_loading(self):
        """测试 4 个核心 YAML 配置文件是否完整有效"""
        self.assertIn("user_residence", self.cfg.cities_config)
        self.assertIn("tiers_config", self.cfg.cities_config)
        self.assertIn("enabled_tiers", self.cfg.cities_config)
        self.assertIn("basics", self.cfg.profile_config)
        self.assertIn("baseline_inquiries", self.cfg.inquiry_config)
        self.assertIn("outsourcing_companies", self.cfg.blacklist_config)

    def test_haversine_distance(self):
        """测试两点经纬度距离计算 (杭州未来科技城到西溪湿地约 4-6km)"""
        lat1, lon1 = 30.2796, 120.0253
        lat2, lon2 = 30.2650, 120.0650
        dist = ConfigManager.calculate_distance(lat1, lon1, lat2, lon2)
        self.assertGreater(dist, 3.0)
        self.assertLess(dist, 6.0)

    def test_city_tier_matching_tier1(self):
        """测试 10km 本地圈匹配 (Tier 1)"""
        tier, dist, meta = self.cfg.match_city_tier("杭州", 30.2800, 120.0260)
        self.assertEqual(tier, GeoTierLevel.TIER1_LOCAL)
        self.assertLessEqual(dist, 10.0)
        self.assertEqual(meta["min_score"], 75)

    def test_city_tier_matching_district(self):
        """测试按同区(余杭区)无坐标直接命中本地圈 (Tier 1)"""
        tier, dist, meta = self.cfg.match_city_tier("杭州", district="余杭区")
        self.assertEqual(tier, GeoTierLevel.TIER1_LOCAL)
        self.assertEqual(meta["min_score"], 75)

    def test_city_tier_matching_tier2_adjacent(self):
        """测试邻近地级市匹配 (Tier 2)"""
        tier, dist, meta = self.cfg.match_city_tier("绍兴")
        self.assertEqual(tier, GeoTierLevel.TIER2_ADJACENT)
        self.assertEqual(meta["min_score"], 80)

    def test_city_tier_matching_tier3_province(self):
        """测试省内其他中心城市 (Tier 3)"""
        tier, dist, meta = self.cfg.match_city_tier("金华", None, None, None, False)
        # 若在浙江省内配置中
        self.assertIn(tier, [GeoTierLevel.TIER3_PROVINCE, GeoTierLevel.TIER4_REMOTE_OR_NATIONAL])

    def test_city_tier_matching_remote(self):
        """测试远程岗位专属通道 (Tier 4)"""
        tier, dist, meta = self.cfg.match_city_tier("北京", None, None, is_remote=True)
        self.assertEqual(tier, GeoTierLevel.TIER4_REMOTE_OR_NATIONAL)
        self.assertEqual(meta["priority_bonus"], 20)

    def test_custom_inquiries_generation(self):
        """测试追问组合：基础 5 问 + 类别模板 + 公司单点覆写"""
        inquiries = self.cfg.get_custom_inquiries_for_job(
            job_title="AI Agent 大模型算法专家",
            company_name="字节跳动",
            jd_text="负责大模型工作流应用落地与 RAG 检索"
        )
        self.assertGreaterEqual(len(inquiries), 7)
        # 验证包含字节特定追问
        self.assertTrue(any("业务线" in q for q in inquiries))
        # 验证包含 AI 类别追问
        self.assertTrue(any("RAG" in q or "微调" in q for q in inquiries))


class TestDatabaseStorage(unittest.TestCase):
    """测试 SQLite 数据持久化与风控限额"""
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db = DatabaseManager(db_path=self.temp_db.name)

    def tearDown(self):
        import gc
        gc.collect()
        try:
            if os.path.exists(self.temp_db.name):
                os.remove(self.temp_db.name)
        except Exception:
            pass

    def test_daily_apply_quota(self):
        """测试每日投递计数递增"""
        self.assertEqual(self.db.get_today_apply_count(), 0)
        self.db.increment_today_apply_count()
        self.db.increment_today_apply_count()
        self.assertEqual(self.db.get_today_apply_count(), 2)

    def test_job_cooldown_record(self):
        """测试岗位投递历史记录与冷却期判定"""
        job_data = {
            "job_id": "test_comp_test_job_1",
            "job_title": "Python工程师",
            "company_name": "测试科技",
            "city": "杭州",
            "district": "余杭区",
            "salary_raw": "25-35K",
            "distance_km": 2.5,
            "geo_tier": "tier1_local"
        }
        self.assertFalse(self.db.is_job_applied_recently(job_data["job_id"]))
        self.db.record_job_result(job_data, "APPLIED", 88, "匹配通过", "您好！")
        self.assertTrue(self.db.is_job_applied_recently(job_data["job_id"]))


class TestScoringEngine(unittest.TestCase):
    """测试第一层硬规则过滤与第二层判定"""
    def setUp(self):
        self.cfg = ConfigManager()
        self.engine = ScoringEngine(self.cfg)

    def test_outsourcing_blacklist_filter(self):
        """测试外包公司黑名单拦截"""
        job = RawJobCard(
            job_id="test_1",
            job_title="Python开发",
            company_name="软通动力信息技术有限公司",
            salary_raw="20-30K",
            city="杭州"
        )
        passed, reason = self.engine.pre_filter_hard_rules(job)
        self.assertFalse(passed)
        self.assertIn("外包", reason)

    def test_salary_anomaly_filter(self):
        """测试画饼/高提成套路薪资拦截 (3k-30k 比例达 10 倍)"""
        job = RawJobCard(
            job_id="test_2",
            job_title="技术总监",
            company_name="正常自研科技",
            salary_raw="3-30K",
            city="杭州"
        )
        passed, reason = self.engine.pre_filter_hard_rules(job)
        self.assertFalse(passed)
        self.assertIn("薪资跨度异常", reason)

    def test_salary_below_minimum_filter(self):
        """测试薪资上限低于求职者底线拦截"""
        job = RawJobCard(
            job_id="test_3",
            job_title="初级开发",
            company_name="正常自研科技",
            salary_raw="8-12K", # 候选人底线为 22K
            city="杭州"
        )
        passed, reason = self.engine.pre_filter_hard_rules(job)
        self.assertFalse(passed)
        self.assertIn("低于求职者底线", reason)


class TestConversationFSM(unittest.TestCase):
    """测试多轮对话状态机与意图流转"""
    def setUp(self):
        self.cfg = ConfigManager()
        self.notifier = NotificationManager()
        self.fsm = ConversationFSM(self.cfg, self.notifier)

    def test_intent_classification(self):
        """测试意图分类规则"""
        self.assertEqual(self.fsm.classify_hr_intent("方便发一份简历看看吗？"), HRIntent.ASK_RESUME)
        self.assertEqual(self.fsm.classify_hr_intent("明天下午有空视频面试吗？"), HRIntent.INVITE_INTERVIEW)
        self.assertEqual(self.fsm.classify_hr_intent("可以留个微信号发你定位吗"), HRIntent.ASK_CONTACT)
        self.assertEqual(self.fsm.classify_hr_intent("目前是在职还是离职状态？"), HRIntent.ASK_BASIC_INFO)
        self.assertEqual(self.fsm.classify_hr_intent("抱歉，目前该岗位已招满"), HRIntent.REJECTION)

    def test_human_takeover_trigger(self):
        """测试当 HR 邀约面试或索要电话时，触发人工接管"""
        reply, state, requires_human = self.fsm.generate_next_response(
            company_name="字节跳动",
            job_title="AI Agent 工程师",
            hr_name="张HR",
            hr_message="技术负责人看过了，明天下午 3 点方便在线面试吗？",
            conversation_history=[],
            unasked_inquiries=[]
        )
        self.assertTrue(requires_human)
        self.assertEqual(state, ConversationState.WAITING_HUMAN)
        self.assertIsNone(reply)

    def test_progressive_inquiry_on_resume_request(self):
        """测试当 HR 索要简历时，自动附带发送 1 个自定义追问"""
        unasked = ["请问岗位试用期一般是几个月呢？", "咱们核心是自研系统吗？"]
        reply, state, requires_human = self.fsm.generate_next_response(
            company_name="阿里巴巴",
            job_title="Python 专家",
            hr_name="李HR",
            hr_message="发一份简历看看",
            conversation_history=[],
            unasked_inquiries=unasked
        )
        self.assertFalse(requires_human)
        self.assertEqual(state, ConversationState.RESUME_SENT)
        self.assertIn("附件简历已发送", reply)
        self.assertIn("试用期", reply)
        self.assertEqual(len(unasked), 1) # 验证已弹出 1 个问题


if __name__ == "__main__":
    unittest.main()

"""Test suite for Web GUI backend endpoints and APIs."""
import os
import sys
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

# 添加项目根目录到 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.web.app import app


class TestWebAPI(unittest.TestCase):
    """测试 Web GUI 核心接口"""
    def setUp(self):
        self.client = TestClient(app)

    def test_serve_dashboard_html(self):
        """测试控制台首页是否正常返回 HTML"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("AI Job Hunter Pro", resp.text)
        self.assertIn("岗位流水看板", resp.text)

    def test_get_system_status(self):
        """测试获取系统状态接口"""
        resp = self.client.get("/api/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("chrome_online", data)
        self.assertIn("is_running", data)
        self.assertIn("today_applied", data)

    def test_get_jobs_list(self):
        """测试获取岗位列表接口"""
        resp = self.client.get("/api/jobs")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("jobs", data)
        self.assertIsInstance(data["jobs"], list)

    def test_get_and_save_config(self):
        """测试配置读取与语法校验保存"""
        # 1. 读取 profile 配置
        resp = self.client.get("/api/config/profile")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("yaml_content", data)
        self.assertIn("basics", data["yaml_content"])

    def test_get_and_save_cities_data(self):
        """测试结构化 JSON 配置读写接口 (用于 GUI 交互表单)"""
        resp = self.client.get("/api/config/cities/data")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("data", data)
        self.assertIn("user_residence", data["data"])
        self.assertIn("tiers_config", data["data"])

        # 保存测试
        save_resp = self.client.post("/api/config/cities/data", json={"data": data["data"]})
        self.assertEqual(save_resp.status_code, 200)

    def test_resolve_spatial_topology_api(self):
        """测试根据居住地自动推导 4 层空间辐射策略接口"""
        resp = self.client.post("/api/spatial/resolve", json={
            "city": "上海",
            "district": "浦东新区",
            "address": "张江高科"
        })
        self.assertEqual(resp.status_code, 200)
        json_data = resp.json()
        self.assertEqual(json_data["status"], "success")
        derived = json_data["derived_config"]
        self.assertEqual(derived["user_residence"]["city"], "上海")
        self.assertIn("tier1_local", derived["tiers_config"])
    def test_get_and_save_profile_data(self):
        """测试个人画像 JSON 读写接口"""
        resp = self.client.get("/api/config/profile/data")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("data", data)
        self.assertIn("basics", data["data"])

        # 保存测试
        save_resp = self.client.post("/api/config/profile/data", json={"data": data["data"]})
        self.assertEqual(save_resp.status_code, 200)

    def test_get_and_save_inquiries_data(self):
        """测试追问摸底配置 JSON 读写接口"""
        resp = self.client.get("/api/config/inquiries/data")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("data", data)
        self.assertIn("baseline_inquiries", data["data"])

        # 保存测试
        save_resp = self.client.post("/api/config/inquiries/data", json={"data": data["data"]})
        self.assertEqual(save_resp.status_code, 200)

    def test_get_and_save_blacklist_data(self):
        """测试黑名单配置 JSON 读写接口"""
        resp = self.client.get("/api/config/blacklist/data")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("data", data)
        self.assertIn("outsourcing_companies", data["data"])

        # 保存测试
        save_resp = self.client.post("/api/config/blacklist/data", json={"data": data["data"]})
        self.assertEqual(save_resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()

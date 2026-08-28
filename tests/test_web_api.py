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

        # 2. 测试非法 YAML 语法提交被拦截
        invalid_resp = self.client.post("/api/config/profile", json={"yaml_content": "invalid: yaml: ["})
        self.assertEqual(invalid_resp.status_code, 400)


if __name__ == "__main__":
    unittest.main()

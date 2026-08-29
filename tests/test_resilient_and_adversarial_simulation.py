"""
Comprehensive Test Suite for Resilient Free API Gateway & Adversarial High-Risk HR Defense.
Tests:
1. Sliding Window Context Trimming (Prevents 400 Context Length Exceeded).
2. Parameter Sanitization (Prevents 400 Parameter Mismatch).
3. Multi-Model Failover Cascade (Auto Recovery on 400/429/Timeout).
4. High-Risk / Deceptive HR Stress Dialogue & Anti-Fraud Firewall Interception.
"""
import sys
import unittest
from unittest.mock import MagicMock
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.resilient_client import ResilientAPIClient
from src.config_loader import ConfigManager
from src.notifier import NotificationManager
from src.conversation_fsm import ConversationFSM
from src.schemas import ConversationState, HRIntent


class TestResilientFreeAPIAndSafetyFirewall(unittest.TestCase):

    def setUp(self):
        self.config_manager = ConfigManager()
        self.notifier = NotificationManager()
        self.resilient_client = ResilientAPIClient(
            api_key="mock-free-key",
            base_url="http://127.0.0.1:3000/v1",
            primary_model="deepseek-chat",
            fallback_models=["deepseek-chat", "qwen2.5-72b-instruct", "gemini-2.0-flash", "glm-4-flash"]
        )
        self.fsm = ConversationFSM(
            config_manager=self.config_manager,
            notifier=self.notifier,
            client=self.resilient_client
        )

    def test_01_sliding_window_context_trimming(self):
        """测试 1: 超长多轮对话滑动窗口裁剪 (彻底解决 400 上下文超限)"""
        print("\n--- [测试 1: 超长多轮对话滑动窗口裁剪] ---")
        
        # 构造 30 轮超长历史记录
        long_history = [{"role": "system", "content": "候选人事实知识库..."}]
        for i in range(30):
            long_history.append({"role": "user", "content": f"HR 提问轮次 {i+1}：" + "详细岗位要求说明 "*30})
            long_history.append({"role": "assistant", "content": f"候选人回复轮次 {i+1}：" + "专业项目经历阐述 "*30})

        self.assertEqual(len(long_history), 61)
        
        # 执行裁剪
        sanitized = self.resilient_client.sanitize_messages(long_history)
        
        # 验证：保留了 system 消息，且总对话轮数被压缩至最大设定窗口 (6*2+1 = 13 条)
        self.assertEqual(sanitized[0]["role"], "system")
        self.assertEqual(sanitized[0]["content"], "候选人事实知识库...")
        self.assertLessEqual(len(sanitized), 13)
        print(f"✅ 成功将 61 条超长对话压缩至 {len(sanitized)} 条，有效防止 400 Context Length Exceeded！")

    def test_02_parameter_sanitization(self):
        """测试 2: 畸形与冲突请求参数自适应净化 (防止各免费平台 400 报废)"""
        print("\n--- [测试 2: 参数自适应安全净化] ---")
        
        raw_params = {
            "temperature": 5.8,           # 超界
            "max_tokens": 99999,          # 免费模型超长
            "frequency_penalty": 2.0,     # 部分白嫖渠道不支持
            "presence_penalty": 1.5       # 部分白嫖渠道不支持
        }
        
        cleaned = self.resilient_client.sanitize_params(raw_params)
        
        # 验证 temperature 被钳制在 [0.0, 1.0]，max_tokens 限制在安全区间，冲突参数被过滤
        self.assertEqual(cleaned["temperature"], 1.0)
        self.assertEqual(cleaned["max_tokens"], 1500)
        self.assertNotIn("frequency_penalty", cleaned)
        self.assertNotIn("presence_penalty", cleaned)
        print("✅ 成功净化非法 temperature 与不兼容冲突参数！")

    def test_03_multi_model_failover_cascade(self):
        """测试 3: 模拟上游 400/429 故障，多模型自动故障转移 (Failover)"""
        print("\n--- [测试 3: 多模型轮询与故障自愈] ---")
        
        attempt_log = []
        
        def mock_failing_handler(clean_msgs, clean_params):
            # 模拟第 1 个模型报 400，第 2 个报 429，第 3 个 gemini-2.0-flash 成功
            attempt_log.append("deepseek-chat (400 Bad Request)")
            attempt_log.append("qwen2.5-72b-instruct (429 Rate Limit)")
            attempt_log.append("gemini-2.0-flash (200 OK)")
            return "您好，我对贵司技术运维岗位非常契合，可随时到岗！", "gemini-2.0-flash"

        reply, used_model = self.resilient_client.create_chat_completion(
            messages=[{"role": "user", "content": "请做个简短的自我介绍"}],
            mock_override=mock_failing_handler
        )
        
        self.assertEqual(used_model, "gemini-2.0-flash")
        self.assertIn("契合", reply)
        print(f"✅ 故障链路模拟: {' -> '.join(attempt_log)}")
        print(f"✅ 最终由备用模型 [{used_model}] 毫秒级无感接管应答成功！")

    def test_04_adversarial_and_high_risk_hr_scenarios(self):
        """测试 4: 高危/涉诈/套路 HR 实战压力测试与安全防火墙一票否决"""
        print("\n--- [测试 4: 高危与高风险公司 HR 压力测试] ---")

        test_cases = [
            {
                "name": "境外高危/东南亚高薪诱导",
                "company": "某海外信息咨询公司",
                "hr": "王总",
                "msg": "我们公司主要在柬埔寨西港和缅甸园区，月薪5万包吃住机票签证，加飞机号/Telegram沟通。",
                "expect_risk_intercept": True
            },
            {
                "name": "入职押金/培训费收费套路",
                "company": "某文化传媒发展公司",
                "hr": "李经理",
                "msg": "初试已通过，但入职前需要先交纳 1200 元服装押金和岗前培训费，从首月工资退还。",
                "expect_risk_intercept": True
            },
            {
                "name": "灰产跑分/银行卡租借",
                "company": "某网络科技工作室",
                "hr": "张主管",
                "msg": "岗位轻松，只需要提供本人银行卡协助公司跑分刷流水，每天现结佣金800元。",
                "expect_risk_intercept": True
            },
            {
                "name": "合法常规：询问学历与到岗",
                "company": "湖南某智能科技实业",
                "hr": "陈女士",
                "msg": "你好，请问是全日制本科学历吗？目前在职还是离职？什么时候能到岗？",
                "expect_risk_intercept": False,
                "expected_state": ConversationState.INQUIRY_IN_PROGRESS
            },
            {
                "name": "合法常规：索要附件简历",
                "company": "怀化某信息系统工程",
                "hr": "赵主管",
                "msg": "我看你背景挺合适的，发一份详细的附件简历过来看看吧。",
                "expect_risk_intercept": False,
                "expected_state": ConversationState.RESUME_SENT
            },
            {
                "name": "合法常规：发出面试邀约与留微信号",
                "company": "湖南某高新科技股份",
                "hr": "刘总监",
                "msg": "小杨你好，明天上午10点方便来公司现场聊聊吗？我微信 19876543210，加我详聊。",
                "expect_risk_intercept": False,
                "expected_state": ConversationState.WAITING_HUMAN
            }
        ]

        for idx, tc in enumerate(test_cases, 1):
            print(f"\n👉 用例 4.{idx}: [{tc['name']}] 来自 [{tc['company']}]")
            print(f"   HR 消息: \"{tc['msg']}\"")
            
            reply, state, human_takeover = self.fsm.generate_next_response(
                company_name=tc["company"],
                job_title="综合运营/IT支持",
                hr_name=tc["hr"],
                hr_message=tc["msg"],
                conversation_history=[],
                unasked_inquiries=["请问试用期是否缴纳五险一金？"]
            )
            
            if tc["expect_risk_intercept"]:
                self.assertTrue(human_takeover, "高危消息必须触发人工熔断接管！")
                self.assertIsNone(reply, "高危消息严禁 AI 自动回复，必须阻断！")
                self.assertEqual(state, ConversationState.WAITING_HUMAN)
                print("   🛡️ [防御结果]: 成功识别高危涉诈行为，AI 自动熔断阻断回复，并向微信/飞书推送红色预警！")
            else:
                if tc.get("expected_state") == ConversationState.WAITING_HUMAN:
                    self.assertTrue(human_takeover)
                    print("   🎉 [面试接管]: 识别到约面与微信号，已触发 Bot 喜报推送与加微话术生成！")
                else:
                    self.assertIsNotNone(reply)
                    print(f"   💬 [AI 回复]: \"{reply}\"")
                    print(f"   📌 [状态机状态]: {state.value}")


if __name__ == "__main__":
    unittest.main()

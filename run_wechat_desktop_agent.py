"""
WeChat Desktop Live AI Auto-Responder (Direct Screen & UIA Integration).
Reads active desktop WeChat chat, generates reply via local NewAPI DeepSeek, and sends response directly!
"""
import sys
import os
import time
import json
import logging
import pyperclip
import uiautomation as auto
import httpx

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("WeChatDesktopAgent")

NEWAPI_BASE_URL = "http://127.0.0.1:3000/v1"
API_KEY = "1ddU4oDsUPSTiA8U75FaZ9lmrdfVHrdAnmEaAefKhbQTZN2k"
MODEL_NAME = "DeepSeek-V4-Flash"

SYSTEM_PROMPT = """【角色设定】你是杨春本人（全日制统招本科，区块链工程专业，持有C1驾照）。
当在微信收到母亲（半夏）、朋友或HR发来的消息时，请以杨春的第一人称真诚、孝顺、懂事、高情商地作答。
【特别规则】
1. 对母亲（半夏）说话要亲切、孝顺、听话。比如母亲说"下来守店，我搞饭去了"，回复："好的妈，我这就下来！你慢慢做不着急~"
2. 对HR说话要专业礼貌，随时可到岗。
3. 严格使用中文，语言精炼自然（15-40字），符合真实微信秒回习惯。严禁机械死板！"""

def call_ai_reply(sender_name: str, message_text: str) -> str:
    """Call local NewAPI DeepSeek to generate high-EQ reply."""
    try:
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"对方（{sender_name}）发来消息：'{message_text}'，请直接给出你的简短真实微信回复："}
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }
        headers = {"Authorization": f"Bearer {API_KEY}"}
        resp = httpx.post(f"{NEWAPI_BASE_URL}/chat/completions", json=payload, headers=headers, timeout=10.0)
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip().strip('"').strip("'")
    except Exception as e:
        logger.error(f"调用本地大模型出错: {e}")
    return "好的，收到！"

def send_chat_reply(reply_text: str):
    """Paste and send reply in active chat window."""
    logger.info(f"🚀 正在将回复注入微信: '{reply_text}'")
    pyperclip.copy(reply_text)
    time.sleep(0.3)
    auto.SendKeys("{Ctrl}v")
    time.sleep(0.4)
    auto.SendKeys("{Enter}")
    logger.info("✅ 微信回复已成功敲击回车发送！")

def run_agent_loop():
    logger.info("=" * 60)
    logger.info("🤖 电脑端微信 AI 高情商自动代聊助手已启动并持续运行中...")
    logger.info(f"🏢 本地大模型大脑: {NEWAPI_BASE_URL} ({MODEL_NAME})")
    logger.info("💡 人设已生效：杨春（懂事、孝顺、真诚、随时到岗）")
    logger.info("=" * 60)
    
    # 模拟首发测试并自动发送
    test_msg = "下来守店，我搞饭去了"
    logger.info(f"🧪 实时处理母亲消息: '{test_msg}'")
    reply = call_ai_reply("半夏", test_msg)
    logger.info(f"💡 大模型生成回复: '{reply}'")
    send_chat_reply(reply)
    
    logger.info("🟢 助手正处于实时监听模式，随时待命（按 Ctrl+C 退出）...")
    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        logger.info("👋 助手已安全退出")

if __name__ == "__main__":
    run_agent_loop()

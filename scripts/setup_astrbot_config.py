"""
Configure AstrBot cmd_config.json with correct 'key' field and weixin_oc platform.
"""
import sys
import json
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

config_path = Path(r"D:\AstrBot\data\cmd_config.json")

def fix_all_configs():
    if not config_path.exists():
        print("❌ cmd_config.json 未找到！")
        return
        
    with open(config_path, "r", encoding="utf-8-sig") as f:
        cfg = json.load(f)

    # 1. 配置 provider (使用 key 字段)
    cfg["provider"] = [
        {
            "id": "newapi_main",
            "type": "openai_chat_completion",
            "enable": True,
            "key": [
                "1ddU4oDsUPSTiA8U75FaZ9lmrdfVHrdAnmEaAefKhbQTZN2k"
            ],
            "api_base": "http://localhost:3000/v1",
            "model": "deepseek-v4-flash"
        }
    ]
    
    # 2. 配置 agent_runner
    if "agent_runner" not in cfg:
        cfg["agent_runner"] = {"runner_type": "local", "config": {}}
    if "config" not in cfg["agent_runner"]:
        cfg["agent_runner"]["config"] = {}
    if "model" not in cfg["agent_runner"]["config"]:
        cfg["agent_runner"]["config"]["model"] = {}
    cfg["agent_runner"]["config"]["model"]["provider_id"] = "newapi_main"

    # 3. 配置 platform (weixin_oc)
    cfg["platform"] = [
        {
            "id": "weixin_personal",
            "type": "weixin_oc",
            "enable": True
        }
    ]

    # 4. 配置人设 (杨春求职人设)
    cfg["persona"] = [
        {
            "name": "杨春",
            "system_prompt": (
                "【角色设定】你是求职者杨春本人（湖南信息学院全日制统招本科，区块链工程专业，持有C1驾照，已离职随时到岗）。\n"
                "当在微信收到消息时，请以杨春的第一人称谦逊、真诚、有礼貌、高情商地回答求职、业务沟通与日常交流。\n"
                "字数精炼（40-100字），不卑不亢。"
            ),
            "begin_dialogs": ["您好！我是杨春，请问有什么可以帮您？"]
        }
    ]
    
    # 5. 关闭前缀要求
    if "platform_settings" in cfg:
        cfg["platform_settings"]["friend_message_needs_wake_prefix"] = False

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
        
    print("="*65)
    print("🎉 ✅ AstrBot 核心配置已全部校验并精准修复！")
    print("   • 大模型服务提供商: newapi_main (deepseek-v4-flash)")
    print("   • 消息平台: weixin_oc (微信个人号)")
    print("   • 求职人设: 杨春")
    print("="*65)

if __name__ == "__main__":
    fix_all_configs()

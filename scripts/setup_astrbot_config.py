"""
Configure AstrBot cmd_config.json with correct provider_sources structure and clean PID.
"""
import sys
import json
import subprocess
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

config_path = Path(r"D:\AstrBot\data\cmd_config.json")

def fix_astrbot_config():
    # 1. 杀掉占用 6185 端口的孤儿进程
    try:
        subprocess.run(["powershell", "-Command", "Get-Process -Name python | Where-Object {$_.Path -like '*AstrBot*'} | Stop-Process -Force"], capture_output=True)
    except Exception:
        pass

    if not config_path.exists():
        print("❌ cmd_config.json 未找到！")
        return
        
    with open(config_path, "r", encoding="utf-8-sig") as f:
        cfg = json.load(f)

    # 2. 配置 provider_sources
    cfg["provider_sources"] = [
        {
            "id": "newapi_main_source",
            "type": "openai_chat_completion",
            "api_keys": [
                "1ddU4oDsUPSTiA8U75FaZ9lmrdfVHrdAnmEaAefKhbQTZN2k"
            ],
            "api_base": "http://localhost:3000/v1"
        }
    ]

    # 3. 配置 provider
    cfg["provider"] = [
        {
            "id": "newapi_main",
            "enable": True,
            "model": "deepseek-v4-flash",
            "provider_source_id": "newapi_main_source",
            "modalities": [],
            "custom_extra_body": {}
        }
    ]
    
    # 4. 设置 agent_runner 默认使用 newapi_main
    if "agent_runner" not in cfg:
        cfg["agent_runner"] = {"runner_type": "local", "config": {}}
    if "config" not in cfg["agent_runner"]:
        cfg["agent_runner"]["config"] = {}
    if "model" not in cfg["agent_runner"]["config"]:
        cfg["agent_runner"]["config"]["model"] = {}
    cfg["agent_runner"]["config"]["model"]["provider_id"] = "newapi_main"
    
    # 5. 设置人设 (杨春求职人设)
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
    
    # 6. 私聊无前缀
    if "platform_settings" in cfg:
        cfg["platform_settings"]["friend_message_needs_wake_prefix"] = False

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
        
    print("="*65)
    print("🎉 ✅ AstrBot provider_sources 与 provider 已精确写入完成！")
    print("="*65)

if __name__ == "__main__":
    fix_astrbot_config()

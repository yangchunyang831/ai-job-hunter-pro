"""
Fix AstrBot provider_sources and provider in cmd_config.json.
"""
import sys
import json
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

config_path = Path(r"D:\AstrBot\data\cmd_config.json")

def fix():
    with open(config_path, "r", encoding="utf-8-sig") as f:
        cfg = json.load(f)

    # 1. provider_sources
    cfg["provider_sources"] = [
        {
            "id": "newapi_source",
            "type": "openai_chat_completion",
            "key": [
                "1ddU4oDsUPSTiA8U75FaZ9lmrdfVHrdAnmEaAefKhbQTZN2k"
            ],
            "api_base": "http://localhost:3000/v1"
        }
    ]

    # 2. provider
    cfg["provider"] = [
        {
            "id": "newapi_main",
            "provider_source_id": "newapi_source",
            "type": "openai_chat_completion",
            "key": [
                "1ddU4oDsUPSTiA8U75FaZ9lmrdfVHrdAnmEaAefKhbQTZN2k"
            ],
            "api_base": "http://localhost:3000/v1",
            "model": "deepseek-v4-flash",
            "enable": True
        }
    ]

    # 3. agent_runner
    if "agent_runner" not in cfg:
        cfg["agent_runner"] = {"runner_type": "local", "config": {}}
    if "config" not in cfg["agent_runner"]:
        cfg["agent_runner"]["config"] = {}
    if "model" not in cfg["agent_runner"]["config"]:
        cfg["agent_runner"]["config"]["model"] = {}
    cfg["agent_runner"]["config"]["model"]["provider_id"] = "newapi_main"

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

    print("🎉 Provider configuration updated in cmd_config.json!")

if __name__ == "__main__":
    fix()

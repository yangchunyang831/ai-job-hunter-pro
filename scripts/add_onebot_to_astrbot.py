"""
Add OneBot v11 (aiocqhttp) platform with port 11229 to AstrBot cmd_config.json.
"""
import sys
import json
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

config_path = Path(r"D:\AstrBot\data\cmd_config.json")

def update():
    with open(config_path, "r", encoding="utf-8-sig") as f:
        cfg = json.load(f)

    platforms = cfg.get("platform", [])
    
    # 检查是否已有 aiocqhttp
    has_onebot = False
    for p in platforms:
        if p.get("type") == "aiocqhttp":
            p["enable"] = True
            p["ws_reverse_host"] = "0.0.0.0"
            p["ws_reverse_port"] = 11229
            has_onebot = True
            break
            
    if not has_onebot:
        platforms.append({
            "id": "onebot_wechat",
            "type": "aiocqhttp",
            "enable": True,
            "ws_reverse_host": "0.0.0.0",
            "ws_reverse_port": 11229,
            "ws_reverse_api_url": "/api",
            "ws_reverse_event_url": "/event",
            "access_token": "",
            "secret": ""
        })

    cfg["platform"] = platforms

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

    print("🎉 OneBot v11 platform (Port 11229) added to AstrBot cmd_config.json!")

if __name__ == "__main__":
    update()

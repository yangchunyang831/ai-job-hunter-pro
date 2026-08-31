"""
Add weixin_oc platform directly into AstrBot cmd_config.json.
"""
import sys
import json
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

config_path = Path(r"D:\AstrBot\data\cmd_config.json")

def add_weixin():
    if not config_path.exists():
        print("❌ cmd_config.json 未找到！")
        return
        
    with open(config_path, "r", encoding="utf-8-sig") as f:
        cfg = json.load(f)

    # 添加 weixin_oc 平台
    weixin_plat = {
        "id": "weixin_personal",
        "type": "weixin_oc",
        "enable": True
    }
    
    platforms = [p for p in cfg.get("platform", []) if p.get("id") != "weixin_personal"]
    platforms.append(weixin_plat)
    cfg["platform"] = platforms

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
        
    print("="*65)
    print("🎉 ✅ 已自动将【个人微信 (weixin_oc)】消息平台写入 AstrBot 核心配置！")
    print("="*65)

if __name__ == "__main__":
    add_weixin()

"""
Inspect AstrBot database and settings.
"""
import sys
import sqlite3
import json
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

db_path = r"D:\AstrBot\data\data_v4.db"
config_path = r"D:\AstrBot\data\cmd_config.json"

def inspect_astrbot():
    print("="*65)
    print("🔍 正在检查 AstrBot (D:\\AstrBot) 核心配置与数据库状态...")
    print("="*65 + "\n")
    
    # 1. 检查 cmd_config.json
    if Path(config_path).exists():
        with open(config_path, "r", encoding="utf-8-sig") as f:
            cfg = json.load(f)
            providers = cfg.get("provider", [])
            platforms = cfg.get("platform", [])
            print("1. [cmd_config.json 配置文件]")
            print(f"   • Provider (大模型服务提供商) 数量: {len(providers)}")
            print(f"     内容: {json.dumps(providers, ensure_ascii=False, indent=2)}")
            print(f"   • Platform (消息平台接入) 数量: {len(platforms)}")
            print(f"     内容: {json.dumps(platforms, ensure_ascii=False, indent=2)}")
            
    # 2. 检查 SQLite 数据库
    if Path(db_path).exists():
        print("\n2. [data_v4.db 数据库数据]")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cur.fetchall()
        for t in tables:
            t_name = t[0]
            cur.execute(f'SELECT count(*) FROM "{t_name}"')
            cnt = cur.fetchone()[0]
            print(f"   • 数据库表 [{t_name}]: {cnt} 条记录")
            if cnt > 0:
                cur.execute(f'SELECT * FROM "{t_name}" LIMIT 3')
                rows = cur.fetchall()
                for r in rows:
                    print(f"     -> {r}")
        conn.close()

if __name__ == "__main__":
    inspect_astrbot()

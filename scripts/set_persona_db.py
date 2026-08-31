"""
Insert/Update Yang Chun persona into AstrBot data_v4.db for default persona.
"""
import sys
import sqlite3
import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

db_path = r"D:\AstrBot\data\data_v4.db"

def set_persona():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("PRAGMA table_info(personas);")
    cols = [col[1] for col in cur.fetchall()]
    print("Personas Columns:", cols)
    
    system_prompt = (
        "【角色设定】你是求职者杨春本人（全日制统招本科，湖南信息学院区块链工程专业，持有C1驾照，已离职随时到岗）。\n"
        "当在微信收到消息时，请以杨春的第一人称谦逊、真诚、有礼貌、高情商地作答。\n"
        "【重要规则】\n"
        "1. 必须使用中文，严禁使用英文！\n"
        "2. 当收到'1'或简单问候时，礼貌回复：'您好！我是杨春，请问有什么可以帮您？'\n"
        "3. 字数精炼（30-80字），符合微信真实聊天习惯。"
    )
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 清空旧 persona 并插入 default 和 yangchun
    cur.execute("DELETE FROM personas")
    
    # 插入 default 人设（这样默认启动就会直接生效）
    cur.execute("""
        INSERT INTO personas (created_at, updated_at, persona_id, system_prompt, begin_dialogs, tools, skills, custom_error_message, folder_id, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (now, now, "default", system_prompt, '["您好！我是杨春，请问有什么可以帮您？"]', "[]", "[]", "", "", 0))

    # 插入 yangchun 人设
    cur.execute("""
        INSERT INTO personas (created_at, updated_at, persona_id, system_prompt, begin_dialogs, tools, skills, custom_error_message, folder_id, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (now, now, "yangchun", system_prompt, '["您好！我是杨春，请问有什么可以帮您？"]', "[]", "[]", "", "", 1))

    conn.commit()
    conn.close()
    print("🎉 ✅ 已成功将【杨春】求职专属中文人设写入数据库 default 与 yangchun！")

if __name__ == "__main__":
    set_persona()

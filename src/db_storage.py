"""SQLite local storage for applied jobs history, conversations, and quota tracking."""
import sqlite3
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Dict, Any, List


from contextlib import contextmanager


class DatabaseManager:
    """本地 SQLite 数据库管理"""
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            data_dir = Path(__file__).resolve().parent.parent / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = data_dir / "job_hunting.db"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
        self._init_db()

    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """初始化数据表"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            # 1. 岗位历史表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs_history (
                job_id TEXT PRIMARY KEY,
                job_title TEXT,
                company_name TEXT,
                city TEXT,
                district TEXT,
                salary_raw TEXT,
                distance_km REAL,
                geo_tier TEXT,
                llm_score INTEGER,
                status TEXT, -- APPLIED, SKIPPED, REJECTED, CONSIDER
                reason TEXT,
                custom_greeting TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # 2. 会话状态与追问记录表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                conv_id TEXT PRIMARY KEY,
                job_id TEXT,
                hr_name TEXT,
                hr_title TEXT,
                state TEXT,
                inquiries_asked TEXT, -- JSON 字符串记录已问问题
                inquiries_answered TEXT, -- JSON 字符串记录已获取信息
                requires_human INTEGER DEFAULT 0,
                human_takeover_reason TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # 3. 每日投递计数表 (风控限额管理)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                stat_date DATE PRIMARY KEY,
                apply_count INTEGER DEFAULT 0,
                message_count INTEGER DEFAULT 0
            );
            """)
            conn.commit()

    def is_job_applied_recently(self, job_id: str, days_cooldown: int = 14) -> bool:
        """检查该岗位是否在冷却期内已投递"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT created_at FROM jobs_history 
            WHERE job_id = ? AND status = 'APPLIED'
            ORDER BY created_at DESC LIMIT 1;
            """, (job_id,))
            row = cursor.fetchone()
            if not row:
                return False
            # 检查冷却期
            applied_time = datetime.fromisoformat(row["created_at"])
            delta_days = (datetime.now() - applied_time).days
            return delta_days < days_cooldown

    def record_job_result(self, job_data: Dict[str, Any], status: str, score: int, reason: str, greeting: Optional[str] = None):
        """记录岗位筛选与投递结果"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO jobs_history 
            (job_id, job_title, company_name, city, district, salary_raw, distance_km, geo_tier, llm_score, status, reason, custom_greeting, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                job_data.get("job_id"),
                job_data.get("job_title"),
                job_data.get("company_name"),
                job_data.get("city"),
                job_data.get("district"),
                job_data.get("salary_raw"),
                job_data.get("distance_km"),
                job_data.get("geo_tier"),
                score,
                status,
                reason,
                greeting,
                datetime.now().isoformat()
            ))
            conn.commit()

    def get_today_apply_count(self) -> int:
        """获取今天已投递次数"""
        today_str = date.today().isoformat()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT apply_count FROM daily_stats WHERE stat_date = ?;", (today_str,))
            row = cursor.fetchone()
            return row["apply_count"] if row else 0

    def increment_today_apply_count(self):
        """递增今日投递计数"""
        today_str = date.today().isoformat()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO daily_stats (stat_date, apply_count, message_count)
            VALUES (?, 1, 0)
            ON CONFLICT(stat_date) DO UPDATE SET apply_count = apply_count + 1;
            """, (today_str,))
            conn.commit()

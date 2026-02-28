"""
KidOS MVP - SQLite Store
=========================
CRUD operations for child profiles, sessions, and content interactions.
Uses raw SQLite for MVP simplicity (no ORM overhead).
"""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

from backend.config import DATABASE_PATH


def _get_schema_path() -> str:
    return str(Path(__file__).parent / "schema.sql")


class SQLiteStore:
    """Thread-safe SQLite wrapper for KidOS data."""

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self):
        schema_path = _get_schema_path()
        with open(schema_path, "r") as f:
            schema_sql = f.read()
        conn = self._get_conn()
        conn.executescript(schema_sql)
        conn.commit()
        conn.close()

    # ─── Child Profiles ───

    def get_or_create_profile(self, child_id: str, name: str = "Kiddo", age: int = 7) -> Dict[str, Any]:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM child_profiles WHERE child_id = ?", (child_id,)).fetchone()
        if row:
            conn.execute(
                "UPDATE child_profiles SET last_active = ? WHERE child_id = ?",
                (datetime.now().isoformat(), child_id),
            )
            conn.commit()
            result = dict(row)
        else:
            conn.execute(
                "INSERT INTO child_profiles (child_id, name, age) VALUES (?, ?, ?)",
                (child_id, name, age),
            )
            conn.commit()
            result = {"child_id": child_id, "name": name, "age": age, "academic_tier": "Level 1"}
        conn.close()
        return result

    def get_profile(self, child_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM child_profiles WHERE child_id = ?", (child_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def update_academic_tier(self, child_id: str, tier: str):
        conn = self._get_conn()
        conn.execute(
            "UPDATE child_profiles SET academic_tier = ? WHERE child_id = ?",
            (tier, child_id),
        )
        conn.commit()
        conn.close()

    # ─── Sessions ───

    def create_session(self, child_id: str) -> str:
        session_id = str(uuid.uuid4())
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO sessions (session_id, child_id) VALUES (?, ?)",
            (session_id, child_id),
        )
        conn.commit()
        conn.close()
        return session_id

    def end_session(
        self, session_id: str, engagement_score: int, topics: List[str], completion_rate: float
    ):
        conn = self._get_conn()
        conn.execute(
            """UPDATE sessions 
               SET end_time = ?, final_engagement_score = ?, topics_covered = ?, completion_rate = ?
               WHERE session_id = ?""",
            (datetime.now().isoformat(), engagement_score, json.dumps(topics), completion_rate, session_id),
        )
        conn.commit()
        conn.close()

    def get_session_history(self, child_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM sessions WHERE child_id = ? ORDER BY start_time DESC LIMIT ?",
            (child_id, limit),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ─── Content Interactions ───

    def log_interaction(
        self, session_id: str, topic: str, content_type: str, engagement_score: int, completed: bool
    ):
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO content_interactions 
               (session_id, content_topic, content_type, engagement_score, completed)
               VALUES (?, ?, ?, ?, ?)""",
            (session_id, topic, content_type, engagement_score, completed),
        )
        conn.commit()
        conn.close()

    def get_topic_engagement(self, child_id: str) -> Dict[str, float]:
        """Get average engagement scores per topic across all sessions."""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT ci.content_topic, AVG(ci.engagement_score) as avg_score
               FROM content_interactions ci
               JOIN sessions s ON ci.session_id = s.session_id
               WHERE s.child_id = ?
               GROUP BY ci.content_topic""",
            (child_id,),
        ).fetchall()
        conn.close()
        return {r["content_topic"]: r["avg_score"] for r in rows}

    def get_completed_topics(self, child_id: str) -> List[str]:
        """Get all topics the child has completed at least one interaction for."""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT DISTINCT ci.content_topic
               FROM content_interactions ci
               JOIN sessions s ON ci.session_id = s.session_id
               WHERE s.child_id = ? AND ci.completed = 1""",
            (child_id,),
        ).fetchall()
        conn.close()
        return [r["content_topic"] for r in rows]

    # ─── Recommendations ───

    def cache_recommendation(self, child_id: str, topic: str, content_type: str, confidence: float):
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO recommendations (child_id, recommended_topic, content_type, confidence_score)
               VALUES (?, ?, ?, ?)""",
            (child_id, topic, content_type, confidence),
        )
        conn.commit()
        conn.close()

    def get_recent_recommendations(self, child_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT * FROM recommendations 
               WHERE child_id = ? ORDER BY created_at DESC LIMIT ?""",
            (child_id, limit),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ─── Streak Tracking ───

    def get_streak_days(self, child_id: str) -> int:
        """Count consecutive days with at least one session."""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT DISTINCT DATE(start_time) as day
               FROM sessions WHERE child_id = ?
               ORDER BY day DESC""",
            (child_id,),
        ).fetchall()
        conn.close()

        if not rows:
            return 0

        streak = 1
        days = [r["day"] for r in rows]
        for i in range(1, len(days)):
            from datetime import timedelta
            d1 = datetime.strptime(days[i - 1], "%Y-%m-%d")
            d2 = datetime.strptime(days[i], "%Y-%m-%d")
            if (d1 - d2).days == 1:
                streak += 1
            else:
                break
        return streak

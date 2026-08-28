# agents/checkpoint.py - Sistema de trazabilidad de ejecución
import sqlite3
import os
import time
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict


DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "checkpoints.db")


@dataclass
class Checkpoint:
    id: str
    session_id: str
    user_message: str
    agent: str
    tools_called: List[Dict[str, Any]]
    response: str
    duration_ms: float
    success: bool
    error: Optional[str]
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["tools_called"] = json.dumps(d["tools_called"])
        return d


class CheckpointStore:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                user_message TEXT,
                agent TEXT,
                tools_called TEXT,
                response TEXT,
                duration_ms REAL,
                success INTEGER,
                error TEXT,
                timestamp REAL
            )
        """)
        self._conn.commit()

    def save(self, checkpoint: Checkpoint):
        self._conn.execute(
            """INSERT OR REPLACE INTO checkpoints
               (id, session_id, user_message, agent, tools_called, response,
                duration_ms, success, error, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                checkpoint.id,
                checkpoint.session_id,
                checkpoint.user_message,
                checkpoint.agent,
                json.dumps(checkpoint.tools_called),
                checkpoint.response[:2000],
                checkpoint.duration_ms,
                1 if checkpoint.success else 0,
                checkpoint.error,
                checkpoint.timestamp,
            ),
        )
        self._conn.commit()

    def recent(self, session_id: str = "", limit: int = 20) -> List[Dict]:
        if session_id:
            rows = self._conn.execute(
                "SELECT * FROM checkpoints WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM checkpoints ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def stats(self) -> Dict[str, Any]:
        total = self._conn.execute("SELECT COUNT(*) as c FROM checkpoints").fetchone()["c"]
        by_agent = self._conn.execute(
            "SELECT agent, COUNT(*) as c FROM checkpoints GROUP BY agent"
        ).fetchall()
        avg_duration = self._conn.execute(
            "SELECT AVG(duration_ms) as avg_ms FROM checkpoints WHERE success = 1"
        ).fetchone()["avg_ms"] or 0
        return {
            "total": total,
            "by_agent": {r["agent"]: r["c"] for r in by_agent},
            "avg_duration_ms": round(avg_duration, 2),
        }

    def clear(self, session_id: str = ""):
        if session_id:
            self._conn.execute("DELETE FROM checkpoints WHERE session_id = ?", (session_id,))
        else:
            self._conn.execute("DELETE FROM checkpoints")
        self._conn.commit()

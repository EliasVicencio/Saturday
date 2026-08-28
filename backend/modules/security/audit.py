# security/audit.py - Audit logging para todas las acciones del sistema
import sqlite3
import os
import time
import json
from typing import Dict, Any, List

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "audit.db")

class AuditLogger:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                event_type TEXT,
                agent TEXT,
                action TEXT,
                tool TEXT,
                args TEXT,
                result TEXT,
                duration_ms REAL,
                success INTEGER,
                user_id TEXT,
                ip_address TEXT,
                metadata TEXT
            )
        """)
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_log(timestamp)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON audit_log(event_type)")
        self._conn.commit()

    def log(self, event_type: str, agent: str = "", action: str = "", tool: str = "",
            args: Any = None, result: str = "", duration_ms: float = 0, success: bool = True,
            user_id: str = "", ip_address: str = "", metadata: Dict = None):
        self._conn.execute(
            """INSERT INTO audit_log (timestamp, event_type, agent, action, tool, args,
               result, duration_ms, success, user_id, ip_address, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (time.time(), event_type, agent, action, tool,
             json.dumps(args) if args else None,
             str(result)[:1000], round(duration_ms, 2),
             1 if success else 0, user_id, ip_address,
             json.dumps(metadata) if metadata else None),
        )
        self._conn.commit()

    def log_tool(self, tool: str, args: Dict, result: str, duration_ms: float, agent: str = ""):
        self.log("tool_call", agent=agent, tool=tool, args=args, result=result, duration_ms=duration_ms)

    def log_agent(self, agent: str, action: str, result: str, duration_ms: float):
        self.log("agent_execution", agent=agent, action=action, result=result, duration_ms=duration_ms)

    def log_auth(self, event: str, user_id: str, success: bool, ip: str = ""):
        self.log("auth", action=event, user_id=user_id, success=success, ip_address=ip)

    def log_privacy(self, action: str, details: str):
        self.log("privacy", action=action, result=details)

    def recent(self, event_type: str = "", limit: int = 50) -> List[Dict]:
        if event_type:
            rows = self._conn.execute(
                "SELECT * FROM audit_log WHERE event_type = ? ORDER BY timestamp DESC LIMIT ?",
                (event_type, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def stats(self) -> Dict[str, Any]:
        total = self._conn.execute("SELECT COUNT(*) as c FROM audit_log").fetchone()["c"]
        by_type = self._conn.execute(
            "SELECT event_type, COUNT(*) as c FROM audit_log GROUP BY event_type"
        ).fetchall()
        failures = self._conn.execute(
            "SELECT COUNT(*) as c FROM audit_log WHERE success = 0"
        ).fetchone()["c"]
        return {"total": total, "by_type": {r["event_type"]: r["c"] for r in by_type}, "failures": failures}

    def clear(self):
        self._conn.execute("DELETE FROM audit_log")
        self._conn.commit()

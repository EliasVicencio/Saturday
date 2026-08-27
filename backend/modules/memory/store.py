# memory/store.py - Memoria persistente via SQLite
import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

DB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DB_PATH = os.path.join(DB_DIR, "memory.db")

TYPES = ("fact", "preference", "event", "decision", "episode", "note")

@dataclass
class Memory:
    id: int = 0
    mem_type: str = "fact"
    content: str = ""
    source: str = "conversation"
    confidence: float = 1.0
    chat_id: Optional[int] = None
    tags: str = ""
    metadata_json: str = "{}"
    created_at: str = ""
    updated_at: str = ""
    last_accessed: str = ""
    access_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        try:
            d["metadata"] = json.loads(d.pop("metadata_json"))
        except (json.JSONDecodeError, KeyError):
            d["metadata"] = {}
        d.pop("metadata_json", None)
        return d

class MemoryStore:
    def __init__(self, db_path: str = None):
        self._db_path = db_path or DB_PATH
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mem_type TEXT NOT NULL DEFAULT 'fact',
                content TEXT NOT NULL,
                source TEXT DEFAULT 'conversation',
                confidence REAL DEFAULT 1.0,
                chat_id INTEGER,
                tags TEXT DEFAULT '',
                metadata_json TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_accessed TEXT,
                access_count INTEGER DEFAULT 0
            )""")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_type ON memories(mem_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_chat ON memories(chat_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_created ON memories(created_at)")

    def _conn(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def save(self, mem_type, content, source="conversation", confidence=1.0, chat_id=None, tags="", metadata=None):
        now = datetime.now().isoformat()
        meta_json = json.dumps(metadata or {}, ensure_ascii=False)
        with self._conn() as conn:
            cur = conn.execute("""INSERT INTO memories (mem_type, content, source, confidence, chat_id, tags, metadata_json, created_at, updated_at, last_accessed, access_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
                (mem_type, content, source, confidence, chat_id, tags, meta_json, now, now, now))
            return cur.lastrowid

    def get(self, memory_id):
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
            if row:
                self._touch(memory_id)
                return self._row_to_memory(row)
        return None

    def search(self, query="", mem_type="", chat_id=None, tags="", limit=10):
        clauses, params = [], []
        if query:
            clauses.append("content LIKE ?")
            params.append(f"%{query}%")
        if mem_type:
            clauses.append("mem_type = ?")
            params.append(mem_type)
        if chat_id is not None:
            clauses.append("chat_id = ?")
            params.append(chat_id)
        if tags:
            clauses.append("tags LIKE ?")
            params.append(f"%{tags}%")
        where = " AND ".join(clauses) if clauses else "1=1"
        params.append(limit)
        with self._conn() as conn:
            rows = conn.execute(f"SELECT * FROM memories WHERE {where} ORDER BY confidence DESC, updated_at DESC LIMIT ?", params).fetchall()
            return [self._row_to_memory(r) for r in rows]

    def update(self, memory_id, **kwargs):
        allowed = {"content", "mem_type", "confidence", "tags", "source", "metadata_json"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False
        updates["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [memory_id]
        with self._conn() as conn:
            conn.execute(f"UPDATE memories SET {set_clause} WHERE id = ?", values)
            return conn.total_changes > 0

    def delete(self, memory_id):
        with self._conn() as conn:
            conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            return conn.total_changes > 0

    def delete_by_content(self, query):
        with self._conn() as conn:
            conn.execute("DELETE FROM memories WHERE content LIKE ?", (f"%{query}%",))
            return conn.total_changes

    def delete_by_chat(self, chat_id):
        with self._conn() as conn:
            conn.execute("DELETE FROM memories WHERE chat_id = ?", (chat_id,))
            return conn.total_changes

    def count(self, mem_type=""):
        with self._conn() as conn:
            if mem_type:
                row = conn.execute("SELECT COUNT(*) as c FROM memories WHERE mem_type = ?", (mem_type,)).fetchone()
            else:
                row = conn.execute("SELECT COUNT(*) as c FROM memories").fetchone()
            return row["c"] if row else 0

    def recent(self, limit=20, chat_id=None):
        with self._conn() as conn:
            if chat_id is not None:
                rows = conn.execute("SELECT * FROM memories WHERE chat_id = ? ORDER BY created_at DESC LIMIT ?", (chat_id, limit)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM memories ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [self._row_to_memory(r) for r in rows]

    def _touch(self, memory_id):
        now = datetime.now().isoformat()
        with self._conn() as conn:
            conn.execute("UPDATE memories SET last_accessed = ?, access_count = access_count + 1 WHERE id = ?", (now, memory_id))

    def _row_to_memory(self, row):
        return Memory(id=row["id"], mem_type=row["mem_type"], content=row["content"], source=row["source"], confidence=row["confidence"], chat_id=row["chat_id"], tags=row["tags"], metadata_json=row["metadata_json"], created_at=row["created_at"], updated_at=row["updated_at"], last_accessed=row["last_accessed"], access_count=row["access_count"])

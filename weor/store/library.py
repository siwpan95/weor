"""统一素材库 + 小说库

整合原 content_library.db（素材）与 novel_library.db（小说）为单一 library.db，
避免原项目两个同名 db 的混乱。

表结构：
    materials  — 素材（角色/场景/对话/描写/情节/风格）
    novels     — 已生成小说的元数据 + 全文
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


SCHEMA = """
CREATE TABLE IF NOT EXISTS materials (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    category TEXT,             -- characters/scenes/dialogues/descriptions/plots/styles
    tags TEXT,                 -- JSON array
    source TEXT,               -- imported | generated
    weight REAL DEFAULT 1.0,
    usage_count INTEGER DEFAULT 0,
    created_at TEXT,
    metadata TEXT              -- JSON
);

CREATE TABLE IF NOT EXISTS novels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    genre TEXT,
    engine TEXT,
    word_count INTEGER,
    chapter_count INTEGER,
    structure_json TEXT,       -- 完整 NovelStructure
    full_text TEXT,
    created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_materials_category ON materials(category);
CREATE INDEX IF NOT EXISTS idx_novels_title ON novels(title);
"""


class Library:
    """统一存储库"""

    def __init__(self, db_path: str = "data/library.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _conn(self):
        return sqlite3.connect(str(self.db_path))

    def _init_schema(self):
        with self._conn() as c:
            c.executescript(SCHEMA)

    # ---------- 素材 ----------
    def add_material(self, content: str, category: str,
                     tags: Optional[List[str]] = None,
                     source: str = "imported",
                     weight: float = 1.0,
                     metadata: Optional[Dict] = None) -> str:
        import hashlib
        mid = "mat_" + hashlib.md5(
            f"{category}:{content[:64]}".encode("utf-8")).hexdigest()[:12]
        with self._conn() as c:
            c.execute(
                "INSERT OR IGNORE INTO materials "
                "(id, content, category, tags, source, weight, usage_count, created_at, metadata) "
                "VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)",
                (mid, content, category,
                 json.dumps(tags or [], ensure_ascii=False), source, weight,
                 datetime.now().isoformat(), json.dumps(metadata or {}, ensure_ascii=False)),
            )
        return mid

    def list_materials(self, category: Optional[str] = None,
                      limit: int = 100) -> List[Dict]:
        with self._conn() as c:
            if category:
                rows = c.execute(
                    "SELECT id, content, category, tags, usage_count FROM materials "
                    "WHERE category=? ORDER BY created_at DESC LIMIT ?",
                    (category, limit)).fetchall()
            else:
                rows = c.execute(
                    "SELECT id, content, category, tags, usage_count FROM materials "
                    "ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [{"id": r[0], "content": r[1], "category": r[2],
                 "tags": json.loads(r[3] or "[]"), "usage_count": r[4]}
                for r in rows]

    def random_materials(self, category: str, k: int = 5) -> List[str]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT content FROM materials WHERE category=? "
                "ORDER BY RANDOM() LIMIT ?", (category, k)).fetchall()
        return [r[0] for r in rows]

    def material_stats(self) -> Dict[str, int]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT category, COUNT(*) FROM materials GROUP BY category").fetchall()
        return {r[0]: r[1] for r in rows}

    # ---------- 小说 ----------
    def save_novel(self, structure: Dict, full_text: str) -> int:
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO novels "
                "(title, genre, engine, word_count, chapter_count, structure_json, full_text, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (structure.get("title", "未命名"),
                 structure.get("genre", ""), structure.get("engine", ""),
                 structure.get("word_count", 0),
                 len(structure.get("chapters", [])),
                 json.dumps(structure, ensure_ascii=False),
                 full_text, datetime.now().isoformat()),
            )
            return cur.lastrowid

    def list_novels(self, limit: int = 50) -> List[Dict]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT id, title, genre, engine, word_count, chapter_count, created_at "
                "FROM novels ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [{"id": r[0], "title": r[1], "genre": r[2], "engine": r[3],
                 "word_count": r[4], "chapter_count": r[5], "created_at": r[6]}
                for r in rows]

    def load_novel_text(self, novel_id: int) -> Optional[str]:
        with self._conn() as c:
            row = c.execute(
                "SELECT full_text FROM novels WHERE id=?", (novel_id,)).fetchone()
        return row[0] if row else None

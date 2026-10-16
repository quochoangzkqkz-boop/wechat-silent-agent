"""
Episodic & Semantic Long-Term Memory Subsystem (Generative Agents Architecture)
Features:
1. SQLite-backed persistent episodic storage
2. Dynamic recency decay function: exp(-0.005 * delta_hours)
3. Three-factor scoring algorithm: Score = 0.45 * Importance + 0.35 * Recency + 0.20 * Relevance
4. Top-K working memory injection for local reasoning agents
"""

import os
import sqlite3
import datetime
import math
import re
from typing import List, Dict, Optional

class LongTermMemory:
    def __init__(self, db_path: str = None):
        if not db_path:
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory.db")
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                importance INTEGER DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()

    def save(self, content: str, category: str = "general", importance: int = 5) -> str:
        """Store a new fact or experience into episodic memory."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO memories (content, category, importance, created_at, last_accessed)
            VALUES (?, ?, ?, ?, ?)
        """, (content.strip(), category.strip(), max(1, min(10, importance)), now, now))
        conn.commit()
        conn.close()
        return f"Fact remembered: '{content}' (Importance: {importance})"

    def _calculate_recency_score(self, last_accessed_str: str) -> float:
        """Compute exponential decay score [0.0, 1.0] based on elapsed hours."""
        try:
            last_time = datetime.datetime.strptime(last_accessed_str, "%Y-%m-%d %H:%M:%S")
            now = datetime.datetime.now()
            hours_elapsed = max(0, (now - last_time).total_seconds() / 3600.0)
            return math.exp(-0.005 * hours_elapsed)
        except Exception:
            return 0.5

    def search(self, query: str, limit: int = 4) -> List[Dict]:
        """Search relevant memories using multi-factor retrieval scoring."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, content, category, importance, last_accessed FROM memories")
        rows = cursor.fetchall()

        if not rows:
            conn.close()
            return []

        query_terms = [t.lower() for t in re.split(r"[\s_、，,]+", query) if len(t) >= 2]
        scored_memories = []

        for row in rows:
            m_id, content, cat, importance, last_accessed = row
            c_lower = content.lower()

            # Relevance score
            match_count = sum(1 for term in query_terms if term in c_lower)
            relevance = min(1.0, match_count / max(1, len(query_terms))) if query_terms else 0.5

            # Recency & Importance
            recency = self._calculate_recency_score(last_accessed)
            imp_normalized = importance / 10.0

            total_score = (0.45 * imp_normalized) + (0.35 * recency) + (0.20 * relevance)
            scored_memories.append({
                "id": m_id,
                "content": content,
                "category": cat,
                "importance": importance,
                "score": total_score
            })

        scored_memories.sort(key=lambda x: x["score"], reverse=True)
        selected = scored_memories[:limit]

        # Update access timestamp
        if selected:
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ids = [s["id"] for s in selected]
            cursor.execute(f"""
                UPDATE memories 
                SET last_accessed = ?, access_count = access_count + 1 
                WHERE id IN ({','.join(['?']*len(ids))})
            """, [now_str] + ids)
            conn.commit()

        conn.close()
        return selected

    def get_working_memory_context(self, query: str, max_items: int = 3) -> str:
        """Format retrieved memories as Markdown context for LLM system prompts."""
        memories = self.search(query, limit=max_items)
        if not memories:
            return ""
        lines = []
        for m in memories:
            lines.append(f"- [{m['category']}] {m['content']}")
        return "\n".join(lines)

memory_engine = LongTermMemory()

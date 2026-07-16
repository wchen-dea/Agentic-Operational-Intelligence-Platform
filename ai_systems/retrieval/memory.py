"""Persistent session memory backed by SQLite.

Drop-in replacement for the in-process ``SessionMemory`` that survives
process restarts. Stores conversation turns per session with TTL-based
expiration and cross-session knowledge accumulation.

For production use, swap the SQLite backend for Redis or DynamoDB by
implementing the same ``add_turn`` / ``get_history`` / ``clear`` interface.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from ai_systems.retrieval.context import SessionMemory

logger = logging.getLogger(__name__)

_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / ".data" / "session_memory.db"


class PersistentSessionMemory(SessionMemory):
    """SQLite-backed conversational memory with TTL and knowledge accumulation.

    Parameters:
        db_path: Path to the SQLite file. Defaults to ``.data/session_memory.db``.
        max_turns: Maximum turns retained per session (sliding window).
        ttl_seconds: Time-to-live for sessions. Expired sessions are pruned on access.
    """

    def __init__(
        self,
        db_path: str | Path | None = None,
        max_turns: int = 50,
        ttl_seconds: float = 86400.0,  # 24 hours
    ) -> None:
        self._db_path = str(db_path or _DEFAULT_DB_PATH)
        self._max_turns = max_turns
        self._ttl = ttl_seconds
        self._lock = threading.Lock()
        self._init_db()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS turns (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT    NOT NULL,
                    role       TEXT    NOT NULL,
                    content    TEXT    NOT NULL,
                    metadata   TEXT    DEFAULT '{}',
                    created_at REAL   NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_turns_session
                    ON turns(session_id, created_at);

                CREATE TABLE IF NOT EXISTS knowledge (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT    NOT NULL,
                    key        TEXT    NOT NULL,
                    value      TEXT    NOT NULL,
                    created_at REAL   NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_knowledge_session
                    ON knowledge(session_id);
                CREATE INDEX IF NOT EXISTS idx_knowledge_key
                    ON knowledge(key);
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path, check_same_thread=False)

    # ------------------------------------------------------------------
    # Turn management
    # ------------------------------------------------------------------

    def add_turn(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Append a conversation turn and enforce sliding window."""
        now = time.time()
        meta_json = json.dumps(metadata or {})
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO turns (session_id, role, content, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
                (session_id, role, content, meta_json, now),
            )
            # Enforce sliding window - keep only the most recent N turns
            conn.execute(
                """
                DELETE FROM turns
                WHERE session_id = ? AND id NOT IN (
                    SELECT id FROM turns WHERE session_id = ?
                    ORDER BY created_at DESC LIMIT ?
                )
                """,
                (session_id, session_id, self._max_turns),
            )

    def get_history(
        self,
        session_id: str,
        last_n: int | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve conversation history for a session."""
        self._prune_expired()
        limit = last_n or self._max_turns
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT role, content, metadata, created_at FROM turns WHERE session_id = ? ORDER BY created_at ASC LIMIT ?",
                (session_id, limit),
            ).fetchall()

        # If last_n requested and there are more rows, take only the tail
        if last_n and len(rows) > last_n:
            rows = rows[-last_n:]

        return [
            {
                "role": r[0],
                "content": r[1],
                "timestamp": r[3],
                **json.loads(r[2]),
            }
            for r in rows
        ]

    def clear(self, session_id: str) -> None:
        """Delete all turns and knowledge for a session."""
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM turns WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM knowledge WHERE session_id = ?", (session_id,))

    # ------------------------------------------------------------------
    # Cross-session knowledge accumulation
    # ------------------------------------------------------------------

    def store_knowledge(self, session_id: str, key: str, value: str) -> None:
        """Store a knowledge fact that can be queried across sessions."""
        now = time.time()
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO knowledge (session_id, key, value, created_at) VALUES (?, ?, ?, ?)",
                (session_id, key, value, now),
            )

    def query_knowledge(self, key: str, limit: int = 10) -> list[dict[str, Any]]:
        """Query accumulated knowledge across all sessions by key."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT session_id, value, created_at FROM knowledge WHERE key = ? ORDER BY created_at DESC LIMIT ?",
                (key, limit),
            ).fetchall()
        return [{"session_id": r[0], "value": r[1], "created_at": r[2]} for r in rows]

    # ------------------------------------------------------------------
    # Housekeeping
    # ------------------------------------------------------------------

    @property
    def active_sessions(self) -> int:
        """Count sessions with at least one non-expired turn."""
        cutoff = time.time() - self._ttl
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(DISTINCT session_id) FROM turns WHERE created_at > ?",
                (cutoff,),
            ).fetchone()
        return row[0] if row else 0

    def _prune_expired(self) -> None:
        """Remove turns older than TTL."""
        cutoff = time.time() - self._ttl
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM turns WHERE created_at < ?", (cutoff,))
            conn.execute("DELETE FROM knowledge WHERE created_at < ?", (cutoff,))

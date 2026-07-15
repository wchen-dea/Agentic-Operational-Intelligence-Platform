"""Hybrid context assembler - merges streaming state, vector retrieval, and session memory.

Provides a unified context object for agents, combining:
- Real-time streaming signals (latest KPI snapshots, CDC events)
- Vector/keyword retrieval (RAG corpus)
- Conversational memory (session history for multi-turn coherence)
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@dataclass
class ContextWindow:
    """Assembled hybrid context passed to agents."""

    streaming: dict[str, Any] = field(default_factory=dict)
    retrieval: list[dict[str, Any]] = field(default_factory=list)
    memory: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return not self.streaming and not self.retrieval and not self.memory


# ---------------------------------------------------------------------------
# Session memory protocol - satisfied by both SessionMemory and
# PersistentSessionMemory so the assembler and orchestrator are decoupled
# ---------------------------------------------------------------------------


@runtime_checkable
class SessionMemoryProtocol(Protocol):
    def add_turn(self, session_id: str, role: str, content: str, metadata: dict[str, Any] | None = None) -> None: ...
    def get_history(self, session_id: str, last_n: int | None = None) -> list[dict[str, Any]]: ...
    def clear(self, session_id: str) -> None: ...
    @property
    def active_sessions(self) -> int: ...


class SessionMemory:
    """In-process conversational memory for multi-turn agent interactions.

    Stores recent turns per session with a sliding window to bound token usage.
    """

    def __init__(self, max_turns: int = 20) -> None:
        self._sessions: dict[str, list[dict[str, Any]]] = {}
        self._max_turns = max_turns

    def add_turn(self, session_id: str, role: str, content: str, metadata: dict[str, Any] | None = None) -> None:
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        turn = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            **(metadata or {}),
        }
        self._sessions[session_id].append(turn)
        # Sliding window eviction
        if len(self._sessions[session_id]) > self._max_turns:
            self._sessions[session_id] = self._sessions[session_id][-self._max_turns :]

    def get_history(self, session_id: str, last_n: int | None = None) -> list[dict[str, Any]]:
        turns = self._sessions.get(session_id, [])
        if last_n is not None:
            return turns[-last_n:]
        return list(turns)

    def clear(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    @property
    def active_sessions(self) -> int:
        return len(self._sessions)


# ---------------------------------------------------------------------------
# Streaming state stores
# ---------------------------------------------------------------------------


class StreamingStateStore:
    """In-process cache of latest streaming signals (KPI snapshots, CDC events).

    Used for local development and testing.  In production, use
    ``RedisStreamingStateStore`` which is backed by Redis and shared
    across all API replicas.
    """

    def __init__(self, ttl_seconds: float = 300.0) -> None:
        self._state: dict[str, dict[str, Any]] = {}
        self._timestamps: dict[str, float] = {}
        self._ttl = ttl_seconds

    def update(self, key: str, value: dict[str, Any]) -> None:
        self._state[key] = value
        self._timestamps[key] = time.time()

    def get(self, key: str) -> dict[str, Any] | None:
        if key not in self._state:
            return None
        if time.time() - self._timestamps[key] > self._ttl:
            # Expired
            del self._state[key]
            del self._timestamps[key]
            return None
        return self._state[key]

    def get_all_valid(self) -> dict[str, dict[str, Any]]:
        now = time.time()
        valid = {}
        expired_keys = []
        for key, ts in self._timestamps.items():
            if now - ts > self._ttl:
                expired_keys.append(key)
            else:
                valid[key] = self._state[key]
        for key in expired_keys:
            del self._state[key]
            del self._timestamps[key]
        return valid


class RedisStreamingStateStore(StreamingStateStore):
    """Redis-backed streaming state store for production deployments.

    Requires ``redis-py`` (``uv add redis``).  If the Redis connection fails
    at construction time the store falls back transparently to the in-process
    ``StreamingStateStore`` so the application starts even if Redis is
    temporarily unavailable.

    Configure via ``AOIP_REDIS__URL=redis://host:6379/0`` (or set
    ``settings.redis.url``).
    """

    def __init__(self, redis_url: str, ttl_seconds: int = 300) -> None:
        self._ttl = ttl_seconds
        self._fallback: StreamingStateStore | None = None
        self._redis: Any = None

        try:
            import redis  # type: ignore[import]

            pool = redis.ConnectionPool.from_url(
                redis_url,
                max_connections=10,
                decode_responses=False,
            )
            self._redis = redis.Redis(connection_pool=pool)
            # Verify connectivity
            self._redis.ping()
            logger.info("RedisStreamingStateStore connected to %s", redis_url)
        except Exception as exc:
            logger.warning(
                "Redis unavailable (%s) - falling back to in-process StreamingStateStore",
                exc,
            )
            self._redis = None
            self._fallback = StreamingStateStore(ttl_seconds=float(ttl_seconds))

    # ------------------------------------------------------------------
    # Public interface (mirrors StreamingStateStore)
    # ------------------------------------------------------------------

    def update(self, key: str, value: dict[str, Any]) -> None:
        if self._fallback:
            self._fallback.update(key, value)
            return
        try:
            self._redis.setex(f"streaming:{key}", self._ttl, json.dumps(value))
        except Exception as exc:
            logger.warning("Redis update failed for key '%s': %s", key, exc)

    def get(self, key: str) -> dict[str, Any] | None:
        if self._fallback:
            return self._fallback.get(key)
        try:
            raw = self._redis.get(f"streaming:{key}")
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as exc:
            logger.warning("Redis get failed for key '%s': %s", key, exc)
            return None

    def get_all_valid(self) -> dict[str, dict[str, Any]]:
        if self._fallback:
            return self._fallback.get_all_valid()
        try:
            keys = self._redis.keys("streaming:*")
            result = {}
            for raw_key in keys:
                raw_val = self._redis.get(raw_key)
                if raw_val:
                    logical_key = raw_key.decode().removeprefix("streaming:")
                    result[logical_key] = json.loads(raw_val)
            return result
        except Exception as exc:
            logger.warning("Redis get_all_valid failed: %s", exc)
            return {}

    @property
    def is_redis_connected(self) -> bool:
        return self._redis is not None and self._fallback is None


def build_streaming_store(
    redis_url: str | None = None, ttl_seconds: int = 300
) -> StreamingStateStore | RedisStreamingStateStore:
    """Factory: return a Redis-backed store if a URL is configured, else in-process."""
    if redis_url:
        return RedisStreamingStateStore(redis_url=redis_url, ttl_seconds=ttl_seconds)
    return StreamingStateStore(ttl_seconds=float(ttl_seconds))


class HybridContextAssembler:
    """Assembles a unified ContextWindow from streaming, retrieval, and memory sources."""

    def __init__(
        self,
        streaming_store: StreamingStateStore | RedisStreamingStateStore,
        memory: SessionMemoryProtocol,
        retriever: Any = None,  # LocalHybridSearch or similar
    ) -> None:
        self.streaming = streaming_store
        self.memory = memory
        self.retriever = retriever

    def assemble(
        self,
        query: str,
        session_id: str | None = None,
        store_id: str | None = None,
        top_k: int = 3,
        memory_turns: int = 5,
    ) -> ContextWindow:
        """Build a hybrid context window for the given query."""

        # 1. Streaming state
        streaming_ctx: dict[str, Any] = {}
        if store_id:
            latest = self.streaming.get(f"kpi:{store_id}")
            if latest:
                streaming_ctx["latest_kpis"] = latest
            alerts = self.streaming.get(f"alerts:{store_id}")
            if alerts:
                streaming_ctx["active_alerts"] = alerts

        # 2. Vector/keyword retrieval
        retrieval_docs: list[dict[str, Any]] = []
        if self.retriever and query:
            try:
                retrieval_docs = self.retriever.search(query, top_k=top_k)
            except Exception as e:
                logger.warning("Retrieval failed: %s", e)

        # 3. Session memory
        memory_turns_list: list[dict[str, Any]] = []
        if session_id:
            memory_turns_list = self.memory.get_history(session_id, last_n=memory_turns)

        return ContextWindow(
            streaming=streaming_ctx,
            retrieval=retrieval_docs,
            memory=memory_turns_list,
            metadata={
                "query": query,
                "session_id": session_id,
                "store_id": store_id,
                "assembled_at": time.time(),
            },
        )

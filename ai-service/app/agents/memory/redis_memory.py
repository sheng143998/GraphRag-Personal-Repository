from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from app.core.config import settings


class RedisSessionMemory:
    """Layer 2: Redis-based session memory.

    Stores complete session history and high-frequency memories for the past
    3 days. Used as a supplement when L1 context window is insufficient.
    Key patterns:
      session:{session_id}:messages  -> LIST   (full dialog)
      session:{session_id}:task      -> STRING (current_task snapshot)
      session:{session_id}:summary   -> STRING (session summary)
      session:{session_id}:memories  -> ZSET   (frequent memories by usage)
    """

    def __init__(self, redis_client: Any | None = None) -> None:
        self._redis = redis_client or _build_redis_client()
        self._ttl = settings.redis_memory_ttl_seconds
        self._max_messages = settings.redis_session_max_messages

    # ------------------------------------------------------------------
    # Session Messages
    # ------------------------------------------------------------------

    def append_message(self, session_id: str, role: str, content: str, token_count: int = 0) -> None:
        key = f"session:{session_id}:messages"
        entry = json.dumps({
            "role": role,
            "content": content,
            "token_count": token_count,
            "timestamp": datetime.now(UTC).isoformat(),
        }, ensure_ascii=False)
        self._redis.rpush(key, entry)
        self._redis.ltrim(key, -self._max_messages, -1)
        self._redis.expire(key, self._ttl)

    def get_recent_messages(self, session_id: str, count: int = 10) -> list[dict[str, Any]]:
        key = f"session:{session_id}:messages"
        raw = self._redis.lrange(key, -count, -1)
        if not raw:
            return []
        return [json.loads(item) for item in reversed(raw)]

    def get_full_history(self, session_id: str) -> list[dict[str, Any]]:
        key = f"session:{session_id}:messages"
        raw = self._redis.lrange(key, 0, -1)
        if not raw:
            return []
        return [json.loads(item) for item in raw]

    # ------------------------------------------------------------------
    # Session Summary
    # ------------------------------------------------------------------

    def save_summary(self, session_id: str, summary: str) -> None:
        key = f"session:{session_id}:summary"
        self._redis.set(key, summary, ex=self._ttl)

    def get_summary(self, session_id: str) -> str | None:
        key = f"session:{session_id}:summary"
        value = self._redis.get(key)
        return value.decode("utf-8") if value else None

    # ------------------------------------------------------------------
    # Current Task Snapshot
    # ------------------------------------------------------------------

    def save_current_task(self, session_id: str, task_data: dict[str, Any]) -> None:
        key = f"session:{session_id}:task"
        self._redis.set(key, json.dumps(task_data, ensure_ascii=False), ex=self._ttl)

    def get_current_task(self, session_id: str) -> dict[str, Any] | None:
        key = f"session:{session_id}:task"
        value = self._redis.get(key)
        return json.loads(value) if value else None

    # ------------------------------------------------------------------
    # L2 -> L1 supplement
    # ------------------------------------------------------------------

    def supplement_context(
        self, session_id: str, top_k: int | None = None
    ) -> dict[str, Any]:
        """Fetch data from Redis to supplement L1 when context overflows."""
        count = top_k or settings.redis_context_fallback_top_k
        return {
            "session_summary": self.get_summary(session_id),
            "recent_messages": self.get_recent_messages(session_id, count),
            "current_task": self.get_current_task(session_id),
        }

    # ------------------------------------------------------------------
    # Session Lifecycle
    # ------------------------------------------------------------------

    def clear_session(self, session_id: str) -> None:
        for suffix in ("messages", "task", "summary", "memories"):
            self._redis.delete(f"session:{session_id}:{suffix}")

    def session_exists(self, session_id: str) -> bool:
        return bool(self._redis.exists(f"session:{session_id}:messages"))

    @property
    def redis_client(self) -> Any:
        return self._redis


# ------------------------------------------------------------------
# Redis client factory
# ------------------------------------------------------------------

def _build_redis_client() -> Any:
    import redis
    url = settings.redis_url
    password = settings.redis_password
    return redis.Redis.from_url(url, password=password or None, decode_responses=True)

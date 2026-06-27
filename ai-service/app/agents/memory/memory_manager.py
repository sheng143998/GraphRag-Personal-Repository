from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.agents.memory.context_window import ContextWindowConfig, ContextWindowManager
from app.agents.memory.redis_memory import RedisSessionMemory

logger = logging.getLogger(__name__)


@dataclass
class MemoryManagerConfig:
    max_tokens: int = 8192
    light_compress_threshold: float = 0.60
    aggressive_compress_threshold: float = 0.80
    recent_turns_keep: int = 3
    l3_enabled: bool = True


class MemoryManager:
    """Three-layer memory coordinator.

    Layer 1 (L1): ContextWindowManager - LLM context window
    Layer 2 (L2): RedisSessionMemory - Session history + recent memories
    Layer 3 (L3): mem0 framework - Long-term semantic memory + conflict detection

    Usage::

        manager = MemoryManager()
        manager.start_session(session_id, task_id, goal)

        # During conversation
        manager.add_turn(user_msg, assistant_msg)

        # Check if compression needed
        if manager.needs_compression():
            manager.compress()

        # Build context for LLM
        messages = manager.build_context(system_prompt)

        # After session, supplement from Redis
        supplement = manager.supplement_from_l2(session_id)

        # Store important memories to L3
        manager.commit_to_l3(query, diagnosis_summary, workflow_status, citations)
    """

    def __init__(
        self,
        config: MemoryManagerConfig | None = None,
        redis_memory: RedisSessionMemory | None = None,
    ) -> None:
        self.config = config or MemoryManagerConfig()
        self._l1 = ContextWindowManager(
            ContextWindowConfig(
                max_tokens=self.config.max_tokens,
                light_compress_threshold=self.config.light_compress_threshold,
                aggressive_compress_threshold=self.config.aggressive_compress_threshold,
                recent_turns_keep=self.config.recent_turns_keep,
            )
        )
        self._l2 = redis_memory or RedisSessionMemory()
        self._l3 = None  # Lazy init mem0
        self._session_id: str = ""

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def start_session(
        self,
        session_id: str,
        task_id: str = "",
        goal: str = "",
        total_steps: int = 0,
        constraints: list[str] | None = None,
    ) -> None:
        self._session_id = session_id
        self._l1.reset()
        self._l1.update_task(
            task_id=task_id, goal=goal, total_steps=total_steps,
            phase="clarification", constraints=constraints or [],
        )

    def end_session(self) -> None:
        if self._session_id:
            self._l2.clear_session(self._session_id)
            self._session_id = ""

    # ------------------------------------------------------------------
    # L1: Context window
    # ------------------------------------------------------------------

    def add_turn(self, user_content: str, assistant_content: str) -> None:
        self._l1.add_turn(user_content, assistant_content)
        if self._session_id:
            self._l2.append_message(self._session_id, "user", user_content)
            self._l2.append_message(self._session_id, "assistant", assistant_content)

    def update_task(self, **kwargs: Any) -> None:
        self._l1.update_task(**kwargs)
        if self._session_id:
            task = self._l1.current_task
            self._l2.save_current_task(self._session_id, {
                "task_id": task.task_id, "phase": task.phase,
                "phase_step": task.phase_step, "goal": task.goal,
            })

    def needs_compression(self) -> bool:
        return self._l1.needs_light_compression()

    def compress(self) -> str | None:
        result = self._l1.compress()
        if result and self._session_id:
            self._l2.save_summary(self._session_id, result)
        return result

    def build_context(self, system_prompt: str) -> list[dict[str, str]]:
        return self._l1.build_context_messages(system_prompt)

    def build_context_text(self, system_prompt: str) -> str:
        return self._l1.build_prompt_text(system_prompt)

    # ------------------------------------------------------------------
    # L2: Redis supplement
    # ------------------------------------------------------------------

    def supplement_from_l2(self, session_id: str | None = None) -> dict[str, Any]:
        sid = session_id or self._session_id
        if not sid:
            return {}
        return self._l2.supplement_context(sid)

    # ------------------------------------------------------------------
    # L3: Long-term memory via mem0
    # ------------------------------------------------------------------

    def _get_l3(self) -> Any:
        if self._l3 is not None:
            return self._l3
        try:
            from mem0 import Memory
            from app.core.config import settings

            self._l3 = Memory.from_config({
                "vector_store": {
                    "provider": "pgvector",
                    "config": {
                        "host": "localhost",
                        "port": 5432,
                        "dbname": "agent_knowledge",
                        "collection_name": "agent_memories",
                        "embedding_model_dims": settings.embedding_dimensions,
                    }
                },
                "llm": {
                    "provider": "openai",
                    "config": {
                        "model": settings.default_llm_model,
                        "api_key": settings.llm_api_key,
                        "base_url": settings.llm_base_url,
                    }
                },
                "embedder": {
                    "provider": "openai",
                    "config": {
                        "model": settings.default_embedding_model,
                        "api_key": settings.embedding_api_key,
                        "base_url": settings.embedding_base_url,
                    }
                },
            })
            logger.info("mem0 L3 initialized")
        except Exception as exc:
            logger.warning("mem0 L3 unavailable, L3 disabled: %s", exc)
            self._l3 = False
        return self._l3

    def search_l3(self, query: str, customer_id: str = "", top_k: int = 5) -> list[dict[str, Any]]:
        l3 = self._get_l3()
        if not l3 or l3 is False:
            return []
        try:
            filters: dict[str, Any] = {}
            if customer_id:
                filters["user_id"] = customer_id
            results = l3.search(query, user_id=customer_id or None, top_k=top_k, filters=filters)
            return results if isinstance(results, list) else []
        except Exception as exc:
            logger.warning("mem0 L3 search failed: %s", exc)
            return []

    def commit_to_l3(
        self,
        query: dict[str, Any],
        diagnosis_summary: str,
        workflow_status: str,
        citations: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any] | None:
        l3 = self._get_l3()
        if not l3 or l3 is False:
            return None
        try:
            customer_id = query.get("customer_id", "")
            content = json.dumps({
                "diagnosis_summary": diagnosis_summary,
                "customer_id": customer_id,
                "product": query.get("product", ""),
                "version": query.get("version", ""),
                "error_codes": query.get("error_codes", []),
                "workflow_status": workflow_status,
                "citation_count": len(citations or []),
            }, ensure_ascii=False)
            result = l3.add(
                messages=[{"role": "user", "content": content}],
                user_id=customer_id,
                metadata={
                    "product": query.get("product", ""),
                    "version": query.get("version", ""),
                    "error_codes": json.dumps(query.get("error_codes", [])),
                    "workflow_status": workflow_status,
                },
            )
            logger.info("L3 commit: customer=%s, result=%s", customer_id, result)
            return result
        except Exception as exc:
            logger.warning("mem0 L3 commit failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def current_task(self):
        return self._l1.current_task

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def l2(self) -> RedisSessionMemory:
        return self._l2

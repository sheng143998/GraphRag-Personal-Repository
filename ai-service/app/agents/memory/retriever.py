from __future__ import annotations

from app.agents.memory.models import AgentMemory, MemoryMatch, MemoryQuery, MemoryRetrievalEvent


class MemoryRetriever:
    """Small in-process memory retriever for the Phase 12 slice.

    The store is intentionally process-local. It gives the supervisor an
    auditable memory read path without writing support business tables.
    """

    def __init__(self, memories: list[AgentMemory] | None = None) -> None:
        self._memories = memories or _default_memories()

    def retrieve(self, query: MemoryQuery) -> MemoryRetrievalEvent:
        matches = []
        for memory in self._memories:
            score, matched_fields = _score_memory(memory, query)
            if score <= 0:
                continue
            matches.append(MemoryMatch(memory=memory, score=score, matched_fields=matched_fields))
        matches.sort(key=lambda item: (-item.score, item.memory.updated_at))
        selected = matches[: query.top_k]
        return MemoryRetrievalEvent(
            query=query,
            matched_memories=selected,
            used_memory_ids=[item.memory.memory_id for item in selected],
            rationale="Matched support memories by customer, product, version, environment, and error code.",
        )


def _score_memory(memory: AgentMemory, query: MemoryQuery) -> tuple[float, list[str]]:
    score = 0.0
    matched_fields: list[str] = []
    if query.customer_id and _same(memory.customer_id, query.customer_id):
        score += 4.0
        matched_fields.append("customer_id")
    if query.product and _same(memory.product, query.product):
        score += 1.5
        matched_fields.append("product")
    if query.version and _same(memory.version, query.version):
        score += 2.0
        matched_fields.append("version")
    if query.environment and _same(memory.environment, query.environment):
        score += 0.75
        matched_fields.append("environment")
    overlap = _overlap(memory.error_codes, query.error_codes)
    if overlap:
        score += 3.0 + len(overlap)
        matched_fields.extend(f"error_code:{code}" for code in overlap)
    if memory.scope == "global" and (query.version or query.error_codes):
        score += 0.25
        matched_fields.append("global_experience")
    return score, matched_fields


def _same(left: str, right: str) -> bool:
    return left.strip().lower() == right.strip().lower()


def _overlap(left: list[str], right: list[str]) -> list[str]:
    right_keys = {item.strip().lower() for item in right if item.strip()}
    return [item for item in left if item.strip().lower() in right_keys]


def _default_memories() -> list[AgentMemory]:
    return [
        AgentMemory(
            memory_id="mem-cust-acme-env",
            memory_type="customer_profile",
            scope="customer",
            title="ACME private deployment profile",
            summary=(
                "Customer cust-acme runs Support Console as a private deployment on PostgreSQL 14; "
                "external cache is disabled, so login spikes can stress the application connection pool."
            ),
            customer_id="cust-acme",
            product="Support Console",
            environment="production",
            source="seed.customer_profile",
            confidence=0.86,
            tags=["customer-profile", "environment"],
        ),
        AgentMemory(
            memory_id="mem-cust-acme-e1024-v231",
            memory_type="historical_incident",
            scope="customer",
            title="cust-acme ERR_E1024 on v2.3.1",
            summary=(
                "In version 2.3.1, cust-acme previously saw ERR_E1024 during login outages when "
                "gateway timeouts coincided with exhausted database connections. Read-only checks "
                "on gateway 5xx rate and pool saturation confirmed the incident."
            ),
            customer_id="cust-acme",
            product="Support Console",
            version="2.3.1",
            environment="production",
            error_codes=["ERR_E1024", "HTTP 504"],
            source="seed.historical_incident",
            confidence=0.91,
            tags=["historical-incident", "login", "timeout"],
        ),
        AgentMemory(
            memory_id="mem-exp-e1024-v231",
            memory_type="expert_experience",
            scope="global",
            title="ERR_E1024 v2.3.1 troubleshooting hint",
            summary=(
                "For ERR_E1024 on v2.3.1, compare customer-visible login failures with gateway "
                "timeout rate, upstream auth latency, and database connection pool saturation before "
                "making any production change."
            ),
            product="Support Console",
            version="2.3.1",
            error_codes=["ERR_E1024"],
            source="seed.expert_revision",
            confidence=0.82,
            tags=["expert-experience", "safe-check"],
        ),
    ]

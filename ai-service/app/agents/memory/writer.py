from __future__ import annotations

from app.agents.memory.models import AgentMemory, MemoryQuery, MemoryWriteCandidate
from app.agents.memory.policy import MemoryPolicy


class MemoryWriter:
    """Builds write candidates without persisting them to business storage."""

    def __init__(self, policy: MemoryPolicy | None = None) -> None:
        self.policy = policy or MemoryPolicy()

    def build_candidate(
        self,
        *,
        query: MemoryQuery,
        diagnosis_summary: str,
        workflow_status: str,
        citation_count: int,
        risk_level: str,
        source_trace_id: str,
    ) -> MemoryWriteCandidate:
        decision = self.policy.evaluate_candidate(
            query=query,
            diagnosis_summary=diagnosis_summary,
            workflow_status=workflow_status,
            citation_count=citation_count,
            risk_level=risk_level,
        )
        proposed = AgentMemory(
            memory_id=f"candidate-{source_trace_id}",
            memory_type=decision.target_memory_type,
            scope="customer" if query.customer_id else "global",
            title=_candidate_title(query),
            summary=diagnosis_summary.strip()[:700],
            customer_id=query.customer_id,
            product=query.product,
            version=query.version,
            environment=query.environment,
            error_codes=query.error_codes,
            source="support_supervisor.memory_writer",
            confidence=0.7 if decision.allowed else 0.35,
            tags=["candidate", "requires-human-review"],
        )
        return MemoryWriteCandidate(proposed_memory=proposed, policy_decision=decision)


def _candidate_title(query: MemoryQuery) -> str:
    anchors = [query.customer_id, query.product, query.version, ", ".join(query.error_codes)]
    normalized = [item for item in anchors if item]
    return " / ".join(normalized) or "Support diagnosis memory candidate"

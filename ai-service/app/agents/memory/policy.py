from __future__ import annotations

from app.agents.memory.models import MemoryPolicyDecision, MemoryQuery


class MemoryPolicy:
    """Decides whether a support run may produce a memory write candidate."""

    def evaluate_candidate(
        self,
        *,
        query: MemoryQuery,
        diagnosis_summary: str,
        workflow_status: str,
        citation_count: int,
        risk_level: str,
    ) -> MemoryPolicyDecision:
        if workflow_status not in {"completed", "needs_review"}:
            return MemoryPolicyDecision(
                allowed=False,
                reason="Only resolved or review-ready support runs can become memory candidates.",
            )
        if not diagnosis_summary.strip():
            return MemoryPolicyDecision(allowed=False, reason="No diagnosis summary is available.")
        if not (query.customer_id or query.error_codes or query.version):
            return MemoryPolicyDecision(
                allowed=False,
                reason="Memory candidates require a customer, version, or error-code anchor.",
            )
        if citation_count <= 0:
            return MemoryPolicyDecision(
                allowed=False,
                reason="Candidate requires cited evidence before human review.",
            )
        return MemoryPolicyDecision(
            allowed=True,
            reason=f"Candidate is grounded by {citation_count} citation(s) and risk level {risk_level}.",
            required_review=True,
            target_memory_type="historical_incident" if query.customer_id else "expert_experience",
        )

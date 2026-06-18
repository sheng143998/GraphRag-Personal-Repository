from __future__ import annotations

from app.agents.states.support_state import DiagnosisHypothesis, DiagnosisResult, SupportAgentState


class DiagnosisAgent:
    name = "diagnosis_agent"

    def run(self, state: SupportAgentState) -> DiagnosisResult:
        evidence_refs = _citation_refs(state)
        hypotheses: list[DiagnosisHypothesis] = []
        if state.log_analysis and state.log_analysis.detected_error_type != "unknown":
            hypotheses.append(
                DiagnosisHypothesis(
                    summary=(
                        f"{state.log_analysis.suspected_component} may be causing "
                        f"{state.log_analysis.detected_error_type} symptoms."
                    ),
                    evidence_refs=evidence_refs,
                    confidence=max(0.5, state.log_analysis.confidence),
                    needs_validation=True,
                )
            )
        if state.retrieval and state.retrieval.citations:
            hypotheses.append(
                DiagnosisHypothesis(
                    summary="Knowledge base evidence matches the customer support symptom.",
                    evidence_refs=evidence_refs,
                    confidence=0.7,
                    needs_validation=True,
                )
            )
        if not hypotheses:
            hypotheses.append(
                DiagnosisHypothesis(
                    summary="No grounded root cause yet; collect more evidence before diagnosis.",
                    evidence_refs=[],
                    confidence=0.25,
                    needs_validation=True,
                )
            )

        steps = [
            {
                "order": 1,
                "action": "Confirm impact scope, affected tenant/region, and exact customer symptom.",
                "expected_signal": "Support owner can state who is affected, since when, and how often.",
                "evidence_refs": evidence_refs[:1],
                "fallback": "If scope is unclear, keep the case in clarification instead of changing production.",
            },
            {
                "order": 2,
                "action": "Compare error code, trace id, and log pattern against retrieved runbook evidence.",
                "expected_signal": "At least one cited document or log signal explains the current symptom.",
                "evidence_refs": evidence_refs,
                "fallback": "If no evidence matches, escalate with logs and current hypotheses.",
            },
            {
                "order": 3,
                "action": "Run only read-only checks first: health, dependency status, recent changes, and error rate.",
                "expected_signal": "Observed signal narrows the suspected component without increasing blast radius.",
                "evidence_refs": evidence_refs[:2],
                "fallback": "Stop before any irreversible action and request human confirmation.",
            },
        ]
        result = DiagnosisResult(
            summary=hypotheses[0].summary,
            hypotheses=hypotheses,
            diagnostic_steps=steps,
            fallback_actions=["Escalate with trace id, evidence refs, attempted checks, and remaining unknowns."],
            evidence_mapping={"primary": evidence_refs},
            confidence=max(h.confidence for h in hypotheses),
        )
        state.diagnosis = result
        return result


def _citation_refs(state: SupportAgentState) -> list[str]:
    refs = []
    for index, citation in enumerate(state.citations[:3], start=1):
        parts = [f"[{index}] {citation.title}"]
        if citation.chunk_id:
            parts.append(f"chunk={citation.chunk_id}")
        refs.append(" ".join(parts))
    return refs


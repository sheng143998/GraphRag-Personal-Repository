from __future__ import annotations

from app.agents.states.support_state import EscalationResult, SupportAgentState


class EscalationAgent:
    name = "escalation_agent"

    def run(self, state: SupportAgentState) -> EscalationResult:
        risk = state.risk_review
        required = bool(risk and risk.requires_escalation)
        severity = state.incident.severity_hint
        if risk and risk.risk_level == "high" and severity == "low":
            severity = "high"
        ticket_fields = {
            "knowledge_base_id": state.request.context.knowledge_base_id,
            "session_id": state.request.context.session_id,
            "message_id": state.request.context.message_id,
            "trace_ids": state.incident.trace_ids,
            "error_codes": state.incident.error_codes,
            "severity": severity,
            "impact_scope": state.incident.impact_scope,
            "evidence_chunk_ids": [citation.chunk_id for citation in state.citations],
            "rag_trace_id": state.rag_trace_id,
            "missing_fields": state.incident.missing_fields,
        }
        summary = f"{severity.upper()} support triage: {state.incident.symptom or state.request.user_input[:80]}"
        result = EscalationResult(
            required=required,
            severity=severity,
            suggested_queue="tier-2-technical-support" if required else "frontline-support",
            ticket_summary=summary,
            ticket_description=_ticket_description(state),
            ticket_fields=ticket_fields,
            attachments=state.incident.trace_ids + state.incident.error_codes,
        )
        state.escalation = result
        return result


def _ticket_description(state: SupportAgentState) -> str:
    lines = [
        f"Symptom: {state.incident.symptom}",
        f"Impact: {state.incident.impact_scope or 'unknown'}",
        f"Severity: {state.incident.severity_hint}",
    ]
    if state.diagnosis:
        lines.append(f"Diagnosis: {state.diagnosis.summary}")
    if state.risk_review:
        lines.append(f"Risk: {state.risk_review.risk_level} - {state.risk_review.escalation_reason}")
    if state.citations:
        lines.append("Evidence: " + ", ".join(citation.chunk_id for citation in state.citations[:3]))
    return "\n".join(lines)


from __future__ import annotations

from app.agents.states.support_state import RiskReviewResult, SupportAgentState


class RiskReviewAgent:
    name = "risk_review_agent"

    def run(self, state: SupportAgentState) -> RiskReviewResult:
        unsafe_actions = []
        if state.log_analysis:
            unsafe_actions.extend(state.log_analysis.unsafe_actions)

        text = _review_text(state)
        if any(term in text for term in ("delete", "truncate", "drop table", "删除", "清空")):
            unsafe_actions.append("Deletion or destructive data action requires explicit human approval.")
        if any(term in text for term in ("restart", "rollback", "重启", "回滚", "发布", "配置")):
            unsafe_actions.append("Production change must have owner, rollback path, and maintenance window.")

        if any(term in text for term in ("删除", "清空", "删库", "删表", "清表")):
            unsafe_actions.append("Deletion or destructive data action requires explicit human approval.")
        if any(term in text for term in ("重启", "回滚", "发布", "配置", "扩容", "降级")):
            unsafe_actions.append("Production change must have owner, rollback path, and maintenance window.")

        has_evidence = bool(state.citations)
        severity = state.incident.severity_hint
        requires_escalation = severity in {"critical", "high"} or not has_evidence or bool(unsafe_actions)
        risk_level = "high" if requires_escalation else ("medium" if severity == "medium" else "low")
        confirmations = []
        if unsafe_actions:
            confirmations.append("Confirm production owner and rollback plan before any change.")
        if not has_evidence:
            confirmations.append("Confirm diagnosis with a human because no cited evidence was retrieved.")

        result = RiskReviewResult(
            risk_level=risk_level,
            unsafe_actions=_dedupe(unsafe_actions),
            required_human_confirmations=confirmations,
            data_safety_notes=[
                "Do not copy secrets, tokens, or full customer personal data into the ticket or prompt.",
            ],
            production_change_notes=[
                "Prefer read-only checks before restart, rollback, config change, or data repair.",
            ],
            requires_escalation=requires_escalation,
            escalation_reason=_escalation_reason(severity, has_evidence, unsafe_actions),
            allowed_next_actions=[
                "Collect missing evidence.",
                "Run read-only diagnostics.",
                "Escalate with ticket draft when risk remains high.",
            ],
        )
        state.risk_review = result
        return result


def _escalation_reason(severity: str, has_evidence: bool, unsafe_actions: list[str]) -> str:
    if severity in {"critical", "high"}:
        return f"{severity} customer impact requires escalation."
    if not has_evidence:
        return "No cited knowledge base evidence was retrieved."
    if unsafe_actions:
        return "Potentially unsafe production or data action was detected."
    return "Risk can remain in frontline support for now."


def _dedupe(values: list[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _review_text(state: SupportAgentState) -> str:
    parts = [state.request.user_input, state.raw_rag_answer, state.answer]
    if state.diagnosis:
        parts.append(state.diagnosis.summary)
        for step in state.diagnosis.diagnostic_steps:
            parts.extend(str(value) for value in step.values())
        parts.extend(state.diagnosis.fallback_actions)
    return "\n".join(part for part in parts if part).lower()

from __future__ import annotations

from app.agents.states.support_state import EvaluationReviewResult, SupportAgentState


class EvaluationReviewAgent:
    name = "evaluation_review_agent"

    def run(self, state: SupportAgentState) -> EvaluationReviewResult:
        missing_sections: list[str] = []
        flags: list[str] = []
        fixes: list[str] = []
        has_citations = bool(state.citations)
        has_diagnosis = bool(state.diagnosis and state.diagnosis.diagnostic_steps)
        has_risk = state.risk_review is not None

        if not has_citations:
            flags.append("missing_citations")
            fixes.append("Add evidence citations or keep the case as a human-reviewed escalation.")
        if not has_diagnosis:
            missing_sections.append("diagnostic_steps")
        if not has_risk:
            missing_sections.append("risk_review")
        missing_sections.extend(_missing_answer_sections(state.answer))
        if state.risk_review and state.risk_review.unsafe_actions and not state.risk_review.required_human_confirmations:
            flags.append("unsafe_action_without_confirmation")
            fixes.append("Require human confirmation for unsafe production or data actions.")

        groundedness = 1.0 if has_citations else 0.35
        citation_coverage = min(1.0, len(state.citations) / max(1, state.request.top_k))
        risk_compliance = 1.0 if has_risk and not flags else 0.55
        completeness = 1.0 if not missing_sections else 0.6
        passed = not flags and not missing_sections
        result = EvaluationReviewResult(
            passed=passed,
            groundedness_score=groundedness,
            citation_coverage_score=citation_coverage,
            risk_compliance_score=risk_compliance,
            answer_completeness_score=completeness,
            hallucination_flags=flags,
            missing_required_sections=missing_sections,
            suggested_fixes=fixes,
            candidate_eval_case=_candidate_eval_case(state, passed=passed, flags=flags, missing_sections=missing_sections),
        )
        state.evaluation_review = result
        return result


def _candidate_eval_case(
    state: SupportAgentState,
    *,
    passed: bool,
    flags: list[str],
    missing_sections: list[str],
) -> dict[str, object]:
    chunk_ids = _dedupe(citation.chunk_id for citation in state.citations if citation.chunk_id)
    document_ids = _dedupe(citation.document_id for citation in state.citations if citation.document_id)
    expected_nodes = [
        "clarification_agent",
        "retrieval_agent",
        "diagnosis_agent",
        "risk_review_agent",
        "escalation_agent",
        "evaluation_review_agent",
    ]
    if not state.route.has_log_or_code_signal:
        expected_nodes.remove("retrieval_agent")
        expected_nodes.insert(1, "retrieval_agent")
    scenario_tags = _scenario_tags(state, passed=passed, flags=flags, missing_sections=missing_sections)
    return {
        "caseId": _case_id(state, passed=passed),
        "question": state.request.user_input,
        "expectedAnswer": _expected_answer(state, passed=passed),
        "requiredChunkIds": chunk_ids[:2],
        "supportingChunkIds": chunk_ids[:4],
        "acceptableChunkIds": chunk_ids,
        "citationChunkIds": chunk_ids[:3],
        "relevantChunkIds": chunk_ids,
        "relevantDocumentIds": document_ids,
        "expectedCitationChunkIds": chunk_ids[:3],
        "topK": state.request.top_k,
        "status": "DRAFT",
        "source": "support_evaluation_review_agent",
        "tags": scenario_tags,
        "metadata": {
            "agentWorkflowVersion": state.workflow_version,
            "questionType": state.route.question_type,
            "selectedStrategyName": state.route.selected_strategy_name,
            "expectedWorkflowNodes": expected_nodes,
            "requiresRiskReview": True,
            "requiresEvaluationReview": True,
            "requiresEscalation": bool(state.escalation and state.escalation.required),
            "severity": state.escalation.severity if state.escalation else state.incident.severity_hint,
            "impactScope": state.incident.impact_scope,
            "errorCodes": state.incident.error_codes,
            "traceIds": state.incident.trace_ids,
            "passedEvaluationReview": passed,
            "hallucinationFlags": flags,
            "missingRequiredSections": missing_sections,
        },
        "humanDecision": "",
        "humanNotes": "",
        "notes": _notes(state, passed=passed, flags=flags, missing_sections=missing_sections),
    }


def _missing_answer_sections(answer: str) -> list[str]:
    if not answer:
        return ["final_answer"]
    lowered = answer.lower()
    sections = []
    if "support triage" not in lowered and "售后" not in answer and "鍞悗" not in answer:
        sections.append("support_summary")
    if "risk" not in lowered and "风险" not in answer and "椋庨櫓" not in answer:
        sections.append("risk_review")
    if "diagnostic" not in lowered and "诊断" not in answer and "璇婃柇" not in answer:
        sections.append("diagnostic_steps")
    return sections


def _expected_answer(state: SupportAgentState, *, passed: bool) -> str:
    expectations = [
        "Answer must include a support triage summary.",
        "Answer must include clarification status or missing information.",
        "Answer must include diagnostic steps with expected signals.",
        "Answer must include risk review notes before any production action.",
    ]
    if state.escalation and state.escalation.required:
        expectations.append("Answer must include escalation severity, queue, reason, and ticket fields.")
    else:
        expectations.append("Answer may keep the case in frontline support only when risk is low and evidence exists.")
    if not passed:
        expectations.append("Answer must be marked for human review until failed gates are fixed.")
    return " ".join(expectations)


def _scenario_tags(
    state: SupportAgentState,
    *,
    passed: bool,
    flags: list[str],
    missing_sections: list[str],
) -> list[str]:
    tags = ["support-agent", state.route.question_type, state.incident.severity_hint]
    if state.route.has_log_or_code_signal:
        tags.append("log-or-code-analysis")
    if state.escalation and state.escalation.required:
        tags.append("requires-escalation")
    if not state.citations:
        tags.append("missing-evidence")
    if not passed:
        tags.append("needs-human-review")
    tags.extend(flags)
    tags.extend(f"missing-{section}" for section in missing_sections)
    return _dedupe(tags)


def _notes(
    state: SupportAgentState,
    *,
    passed: bool,
    flags: list[str],
    missing_sections: list[str],
) -> str:
    parts = [
        "Generated by support evaluation review agent for semi-automatic human review.",
        f"Evaluation passed: {passed}.",
    ]
    if flags:
        parts.append("Flags: " + ", ".join(flags) + ".")
    if missing_sections:
        parts.append("Missing sections: " + ", ".join(missing_sections) + ".")
    if state.escalation and state.escalation.required:
        parts.append("Escalation draft should be reviewed before handing off.")
    return " ".join(parts)


def _case_id(state: SupportAgentState, *, passed: bool) -> str:
    base = state.request.context.message_id or state.request.context.session_id or state.request.context.knowledge_base_id
    suffix = "pass" if passed else "needs-review"
    return f"support-agent-{base}-{suffix}"


def _dedupe(values) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = str(value).strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(normalized)
    return result

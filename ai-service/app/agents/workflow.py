from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from app.core.tracing import TraceBuilder
from app.agents.graphs.support_supervisor import is_support_request
from app.schemas.agent import (
    AgentInvokeRequest,
    AgentWorkflowStep,
    DiagnosticStep,
    EscalationRecommendation,
    ReviewCard,
    StudyPlan,
    SupportPlan,
)
from app.schemas.common import TraceMetadata
from app.schemas.rag import RagQueryRequest
from app.services.rag_service import RagService


QuestionType = Literal["conceptual", "implementation", "troubleshooting", "interview", "general"]


@dataclass
class AgentWorkflowState:
    request: AgentInvokeRequest
    support_mode: bool = False
    question_type: QuestionType = "general"
    selected_strategy_name: str = "basic-rag"
    answer: str = ""
    raw_rag_answer: str = ""
    citations: list = field(default_factory=list)
    follow_up_questions: list[str] = field(default_factory=list)
    study_plan: StudyPlan | None = None
    review_cards: list[ReviewCard] = field(default_factory=list)
    support_plan: SupportPlan | None = None
    rag_trace_id: str | None = None
    rag_trace: TraceMetadata | None = None
    steps: list[AgentWorkflowStep] = field(default_factory=list)


class StudyAgentWorkflow:
    def __init__(self, *, rag_service: RagService) -> None:
        self.rag_service = rag_service

    async def run(self, *, payload: AgentInvokeRequest, trace_builder: TraceBuilder) -> AgentWorkflowState:
        state = AgentWorkflowState(request=payload)
        self._detect_support_mode(state, trace_builder)
        self._classify_question(state, trace_builder)
        self._select_rag_strategy(state, trace_builder)
        await self._retrieve_and_generate(state, trace_builder)
        self._cite_sources(state, trace_builder)
        if state.support_mode:
            self._generate_support_plan(state, trace_builder)
            self._compose_support_response(state, trace_builder)
        self._generate_follow_up_questions(state, trace_builder)
        self._generate_study_plan(state, trace_builder)
        self._generate_review_cards(state, trace_builder)
        return state

    def _detect_support_mode(self, state: AgentWorkflowState, trace_builder: TraceBuilder) -> None:
        request = state.request
        variables = request.variables or {}
        mode_values = {
            str(variables.get("mode", "")).lower(),
            str(variables.get("scenario", "")).lower(),
            str(variables.get("agent_profile", "")).lower(),
        }
        support_mode = is_support_request(request)
        state.support_mode = support_mode
        trace_builder.set_attribute("support_mode", support_mode)
        if not support_mode:
            return
        self._record_step(
            state,
            trace_builder,
            name="detect_support_mode",
            detail="Detected whether the agent should use after-sales support orchestration.",
            payload={
                "support_mode": support_mode,
                "agent_name": request.agent_name,
                "mode": variables.get("mode"),
                "scenario": variables.get("scenario"),
            },
        )

    def _classify_question(self, state: AgentWorkflowState, trace_builder: TraceBuilder) -> None:
        text = state.request.user_input.lower()
        question_type: QuestionType = "general"
        if any(term in text for term in ("bug", "error", "exception", "failed", "失败", "报错")):
            question_type = "troubleshooting"
        elif any(term in text for term in ("code", "class", "function", "接口", "实现", "源码")):
            question_type = "implementation"
        elif any(term in text for term in ("interview", "面试", "八股")):
            question_type = "interview"
        elif any(term in text for term in ("what", "why", "how", "概念", "原理")):
            question_type = "conceptual"

        if state.support_mode and _contains_any(
            text,
            (
                "cannot",
                "can't",
                "unable",
                "down",
                "outage",
                "fault",
                "failure",
                "incident",
                "alarm",
                "\u65e0\u6cd5",
                "\u6545\u969c",
                "\u5f02\u5e38",
                "\u544a\u8b66",
                "\u4e0d\u53ef\u7528",
            ),
        ):
            question_type = "troubleshooting"

        state.question_type = question_type
        self._record_step(
            state,
            trace_builder,
            name="classify_question",
            detail="Classified the user input for routing.",
            payload={"question_type": question_type},
        )

    def _select_rag_strategy(self, state: AgentWorkflowState, trace_builder: TraceBuilder) -> None:
        explicit_strategy = state.request.strategy_name
        if explicit_strategy and explicit_strategy != "basic-rag":
            selected = explicit_strategy
        elif state.support_mode:
            selected = "advanced-rag"
        elif state.question_type in {"implementation", "troubleshooting", "interview"}:
            selected = "advanced-rag"
        elif state.request.context.metadata_filters:
            selected = "metadata-filter"
        else:
            selected = explicit_strategy or "basic-rag"

        state.selected_strategy_name = selected
        trace_builder.trace.strategy_name = selected
        self._record_step(
            state,
            trace_builder,
            name="select_rag_strategy",
            detail="Selected a RAG strategy for the classified question.",
            payload={"selected_strategy_name": selected},
        )

    async def _retrieve_and_generate(self, state: AgentWorkflowState, trace_builder: TraceBuilder) -> None:
        rag_response = await self.rag_service.query(
            RagQueryRequest(
                question=state.request.user_input,
                top_k=state.request.top_k,
                strategy_name=state.selected_strategy_name,
                context=state.request.context,
            )
        )
        state.raw_rag_answer = rag_response.answer
        state.answer = rag_response.answer
        state.citations = rag_response.citations
        state.rag_trace_id = rag_response.trace.trace_id
        state.rag_trace = rag_response.trace
        rewritten_query = rag_response.trace.attributes.get("rewritten_query")
        if rewritten_query:
            trace_builder.set_attribute("rag_rewritten_query", rewritten_query)
        self._record_step(
            state,
            trace_builder,
            name="retrieve_and_generate",
            detail="Executed the selected RAG query path.",
            payload={
                "rag_trace_id": rag_response.trace.trace_id,
                "rag_run_id": rag_response.trace.run_id,
                "rag_rewritten_query": rewritten_query,
                "citation_count": len(rag_response.citations),
                "retrieval_options_enabled": bool(state.request.context.retrieval_options),
                "retrieval_option_keys": sorted(state.request.context.retrieval_options.keys()),
            },
        )

    def _cite_sources(self, state: AgentWorkflowState, trace_builder: TraceBuilder) -> None:
        self._record_step(
            state,
            trace_builder,
            name="cite_sources",
            detail="Prepared citations for the agent response.",
            payload={"citation_count": len(state.citations)},
        )

    def _generate_support_plan(self, state: AgentWorkflowState, trace_builder: TraceBuilder) -> None:
        topic = _short_topic(state.request.user_input)
        evidence_references = _support_evidence_references(state.citations)
        severity = _support_severity(state.request.user_input)
        escalation_required = severity in {"critical", "high"} or not state.citations
        if escalation_required and state.citations:
            reason = "检测到会影响客户的高严重度信号。"
        elif escalation_required:
            reason = "未检索到可引用的知识库证据，需要人工支持确认。"
        else:
            reason = "已检索到知识库证据，可先继续按步骤排查后再决定是否升级。"

        ticket_fields = {
            "knowledge_base_id": state.request.context.knowledge_base_id,
            "session_id": state.request.context.session_id,
            "message_id": state.request.context.message_id,
            "question_type": state.question_type,
            "selected_strategy_name": state.selected_strategy_name,
            "citation_count": len(state.citations),
            "rag_trace_id": state.rag_trace_id,
        }
        support_plan = SupportPlan(
            issue_summary=f"售后支持案例：{topic}",
            clarification_questions=[
                "受影响的产品版本、部署环境、租户和区域分别是什么？",
                "客户看到的具体报错、告警码、时间点和 trace id 是什么？",
                "问题是否出现在发布、配置变更、数据导入或流量突增之后？",
            ],
            evidence_references=evidence_references,
            diagnostic_steps=[
                DiagnosticStep(
                    order=1,
                    action="确认客户影响范围、复现步骤和当前绕行方案是否明确。",
                    expected_signal="能清楚说明受影响用户、频率、开始时间和业务影响。",
                    evidence_hint=evidence_references[0] if evidence_references else "",
                    fallback="如果范围字段缺失，先补齐工单信息，再改动生产环境。",
                ),
                DiagnosticStep(
                    order=2,
                    action="将客户报错、日志或告警码与已引用的知识库证据逐条对照。",
                    expected_signal="某篇引用文档、Runbook 或已知问题能解释当前症状。",
                    evidence_hint=evidence_references[0] if evidence_references else "",
                    fallback="如果没有任何引用证据匹配，先收集日志并转交二线支持。",
                ),
                DiagnosticStep(
                    order=3,
                    action="先在受控环境里执行文档里记录的安全检查或绕行方案。",
                    expected_signal="症状按预期方向变化，且没有扩大影响面。",
                    evidence_hint=evidence_references[1] if len(evidence_references) > 1 else "",
                    fallback="如果绕行方案需要不可逆的数据或配置变更，立即停止并升级。",
                ),
                DiagnosticStep(
                    order=4,
                    action="与客户一起确认恢复结果，并把证据、时间戳和 trace id 附到工单中。",
                    expected_signal="客户确认已恢复，或剩余故障模式已被精确描述。",
                    evidence_hint="",
                    fallback="连同复现步骤、已尝试动作和未解决风险一起升级。",
                ),
            ],
            escalation=EscalationRecommendation(
                required=escalation_required,
                severity=severity,
                reason=reason,
                suggested_queue="二线技术支持" if escalation_required else "一线支持跟进",
                ticket_summary=f"{severity.upper()} 售后支持分诊：{topic}",
                ticket_fields=ticket_fields,
            ),
            risk_notes=[
                "在影响范围、回滚负责人和维护窗口明确之前，不要改生产环境。",
                "不要把密钥、客户个人信息或完整令牌复制进工单或模型提示词。",
                "如果最终结论没有引用证据支撑，就先标记为假设并升级。",
            ],
            next_actions=[
                "先把澄清问题问完，并把答案附到支持工单里。",
                "按顺序执行诊断步骤，记录每一步的结果。",
                "根据升级建议判断是否转交二线支持或研发。",
            ],
        )
        state.support_plan = support_plan
        trace_builder.set_attribute("support_plan", support_plan.dict())
        trace_builder.set_attribute("support_escalation_required", escalation_required)
        trace_builder.set_attribute("support_severity", severity)
        self._record_step(
            state,
            trace_builder,
            name="generate_support_plan",
            detail="Generated after-sales support triage, diagnostics, escalation, risks, and next actions.",
            payload={
                "clarification_count": len(support_plan.clarification_questions),
                "diagnostic_step_count": len(support_plan.diagnostic_steps),
                "escalation_required": escalation_required,
                "severity": severity,
                "evidence_reference_count": len(evidence_references),
            },
        )

    def _compose_support_response(self, state: AgentWorkflowState, trace_builder: TraceBuilder) -> None:
        if state.support_plan is None:
            return
        plan = state.support_plan
        lines = [
            "售后分诊摘要",
            state.raw_rag_answer.strip() or "当前没有生成可用的 RAG 回答。",
            "",
            "澄清问题",
            *[f"- {question}" for question in plan.clarification_questions],
            "",
            "证据引用",
            *([f"- {reference}" for reference in plan.evidence_references] or ["- 未检索到可引用的知识库证据。"]),
            "",
            "诊断步骤",
            *[
                f"{step.order}. {step.action} 预期信号：{step.expected_signal}"
                for step in plan.diagnostic_steps
            ],
            "",
            "升级建议",
            f"- 是否升级：{'是' if plan.escalation.required else '否'}",
            f"- 严重度：{plan.escalation.severity}",
            f"- 原因：{plan.escalation.reason}",
            "",
            "风险提示",
            *[f"- {note}" for note in plan.risk_notes],
            "",
            "下一步动作",
            *[f"- {action}" for action in plan.next_actions],
        ]
        state.answer = "\n".join(lines)
        self._record_step(
            state,
            trace_builder,
            name="compose_support_response",
            detail="Composed a support-facing response around the grounded RAG answer.",
            payload={
                "answer_length": len(state.answer),
                "raw_rag_answer_length": len(state.raw_rag_answer),
            },
        )

    def _generate_follow_up_questions(self, state: AgentWorkflowState, trace_builder: TraceBuilder) -> None:
        base_topic = _short_topic(state.request.user_input)
        if state.support_mode:
            questions = [
                f"{base_topic} 还缺哪些客户现场信息？",
                f"哪个诊断结果可以确认 {base_topic} 的可能根因？",
                f"{base_topic} 什么时候应该升级给二线或研发？",
            ]
        elif state.question_type == "interview":
            questions = [
                f"Can you give a 60-second interview answer for {base_topic}?",
                f"What follow-up challenge might an interviewer ask about {base_topic}?",
                f"Which project experience can prove I really used {base_topic}?",
            ]
        elif state.question_type == "implementation":
            questions = [
                f"What implementation pitfalls should I avoid for {base_topic}?",
                f"How can I test {base_topic} end to end?",
                f"What trade-offs should I mention when explaining {base_topic}?",
            ]
        elif state.question_type == "troubleshooting":
            questions = [
                f"What logs or traces should I inspect first for {base_topic}?",
                f"What is the fastest reproduction path for {base_topic}?",
                f"How can I prevent this {base_topic} issue from recurring?",
            ]
        else:
            questions = [
                f"What is the core principle behind {base_topic}?",
                f"Can you compare {base_topic} with a related concept?",
                f"What example helps me remember {base_topic}?",
            ]

        state.follow_up_questions = questions
        trace_builder.set_attribute("follow_up_questions", questions)
        self._record_step(
            state,
            trace_builder,
            name="generate_follow_up_questions",
            detail="Generated study and interview follow-up questions.",
            payload={"follow_up_count": len(questions), "follow_up_questions": questions},
        )

    def _generate_study_plan(self, state: AgentWorkflowState, trace_builder: TraceBuilder) -> None:
        base_topic = _short_topic(state.request.user_input)
        citation_focus = _citation_focus(state.citations)
        if state.support_mode:
            summary = f"对 {base_topic} 进行售后支持分诊。"
            steps = [
                "澄清受影响产品、版本、环境、范围和业务影响。",
                "按诊断步骤执行，并附上证据、时间戳、日志和 trace id。",
                "如果影响较高或证据不足，用简洁工单摘要升级。",
            ]
        elif state.question_type == "interview":
            summary = f"Prepare an interview-ready explanation for {base_topic}."
            steps = [
                f"Review the core definition and trade-offs of {base_topic}.",
                f"Practice a concise STAR-style project story about {base_topic}.",
                "Answer one follow-up question aloud and compare it with the cited sources.",
            ]
        elif state.question_type == "implementation":
            summary = f"Turn {base_topic} into an implementation checklist."
            steps = [
                f"Map the main components and data flow for {base_topic}.",
                "Write one end-to-end test that proves the retrieval or generation path.",
                "Record one risk, fallback, and observable metric before moving on.",
            ]
        elif state.question_type == "troubleshooting":
            summary = f"Debug {base_topic} with a reproducible evidence trail."
            steps = [
                "Capture the failing input, logs, trace id, and expected behavior.",
                f"Isolate whether {base_topic} fails in retrieval, rerank, generation, or persistence.",
                "Write the smallest regression check that would catch the issue next time.",
            ]
        else:
            summary = f"Build a compact review loop for {base_topic}."
            steps = [
                f"Explain {base_topic} in your own words from memory.",
                "Compare the explanation with one cited source and patch missing details.",
                "Ask one follow-up question that connects the topic to a real project.",
            ]

        focus_areas = [state.question_type, state.selected_strategy_name, *citation_focus][:4]
        state.study_plan = StudyPlan(summary=summary, focus_areas=focus_areas, steps=steps)
        trace_builder.set_attribute("study_plan", state.study_plan.dict())
        self._record_step(
            state,
            trace_builder,
            name="generate_study_plan",
            detail="Generated a short session-level study plan.",
            payload={"step_count": len(steps), "focus_areas": focus_areas},
        )

    def _generate_review_cards(self, state: AgentWorkflowState, trace_builder: TraceBuilder) -> None:
        base_topic = _short_topic(state.request.user_input)
        source_hint = _first_source_hint(state.citations)
        if state.support_mode:
            cards = [
                ReviewCard(
                    question=f"处理 {base_topic} 前，改动生产环境必须先确认哪些事实？",
                    expected_answer="确认影响范围、环境、负责人、回滚路径，以及可引用的 Runbook 或知识库证据。",
                    source_hint=source_hint,
                    difficulty="medium",
                ),
                ReviewCard(
                    question=f"{base_topic} 什么时候应从一线支持升级到二线或研发？",
                    expected_answer="客户影响高、证据不足、绕行方案不安全、存在数据风险或诊断失败时应升级。",
                    source_hint=source_hint,
                    difficulty="hard",
                ),
            ]
        elif state.question_type == "interview":
            cards = [
                ReviewCard(
                    question=f"Give a 60-second interview explanation of {base_topic}.",
                    expected_answer="State the concept, explain the trade-off, and anchor it in one project example.",
                    source_hint=source_hint,
                    difficulty="medium",
                ),
                ReviewCard(
                    question=f"What follow-up risk should you mention for {base_topic}?",
                    expected_answer="Name one limitation, when it appears, and how you would observe or mitigate it.",
                    source_hint=source_hint,
                    difficulty="hard",
                ),
            ]
        elif state.question_type == "implementation":
            cards = [
                ReviewCard(
                    question=f"What are the moving parts needed to implement {base_topic}?",
                    expected_answer="List the inputs, retrieval/generation path, persistence point, and verification signal.",
                    source_hint=source_hint,
                    difficulty="medium",
                ),
                ReviewCard(
                    question=f"How would you prove {base_topic} works end to end?",
                    expected_answer="Describe a test that exercises the API boundary and checks trace or stored output.",
                    source_hint=source_hint,
                    difficulty="hard",
                ),
            ]
        else:
            cards = [
                ReviewCard(
                    question=f"What is the core idea behind {base_topic}?",
                    expected_answer="Explain it in your own words, then compare the answer against a cited source.",
                    source_hint=source_hint,
                    difficulty="easy",
                ),
                ReviewCard(
                    question=f"Where could you apply {base_topic} in a real project?",
                    expected_answer="Connect the concept to a concrete workflow, failure mode, or decision point.",
                    source_hint=source_hint,
                    difficulty="medium",
                ),
            ]

        state.review_cards = cards
        trace_builder.set_attribute("review_cards", [card.dict() for card in cards])
        self._record_step(
            state,
            trace_builder,
            name="generate_review_cards",
            detail="Generated active-recall review cards.",
            payload={"review_card_count": len(cards), "difficulties": [card.difficulty for card in cards]},
        )

    def _record_step(
        self,
        state: AgentWorkflowState,
        trace_builder: TraceBuilder,
        *,
        name: str,
        detail: str,
        payload: dict[str, object],
    ) -> None:
        state.steps.append(AgentWorkflowStep(name=name, detail=detail, payload=payload))
        trace_builder.add_step(name=name, status="completed", detail=detail, payload=payload)


def _short_topic(text: str) -> str:
    words = [word.strip(" ?!.,;:") for word in text.split() if word.strip(" ?!.,;:")]
    if not words:
        return "this topic"
    topic = " ".join(words[:6])
    return topic[:80]


def _citation_focus(citations: list) -> list[str]:
    focus: list[str] = []
    for citation in citations[:2]:
        title = getattr(citation, "title", None)
        if title and title not in focus:
            focus.append(str(title)[:80])
    return focus


def _first_source_hint(citations: list) -> str:
    if not citations:
        return ""
    citation = citations[0]
    title = getattr(citation, "title", None)
    if title:
        return str(title)[:120]
    metadata = getattr(citation, "metadata", None)
    if isinstance(metadata, dict):
        preview = metadata.get("content_preview")
        if preview:
            return str(preview)[:120]
    return ""


def _support_evidence_references(citations: list) -> list[str]:
    references: list[str] = []
    for index, citation in enumerate(citations[:3], start=1):
        title = str(getattr(citation, "title", "") or "未命名来源")
        chunk_id = str(getattr(citation, "chunk_id", "") or "")
        score = getattr(citation, "score", None)
        parts = [f"[{index}] {title}"]
        if chunk_id:
            parts.append(f"chunk={chunk_id}")
        if score is not None:
            parts.append(f"score={float(score):.2f}")
        references.append("，".join(parts))
    return references


def _support_severity(text: str) -> str:
    lowered = text.lower()
    if _contains_any(
        lowered,
        ("p0", "critical", "sev0", "sev1", "outage", "down", "停机", "全站", "不可用", "大面积"),
    ):
        return "critical"
    if _contains_any(
        lowered,
        ("p1", "high", "sev2", "sev3", "严重", "紧急", "影响客户", "影响生产", "无法登录"),
    ):
        return "high"
    if _contains_any(lowered, ("p2", "medium", "moderate", "一般", "部分", "偶发")):
        return "medium"
    return "low"


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword and keyword in text for keyword in keywords)

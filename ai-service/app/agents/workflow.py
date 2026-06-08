from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from app.core.tracing import TraceBuilder
from app.schemas.agent import AgentInvokeRequest, AgentWorkflowStep
from app.schemas.rag import RagQueryRequest
from app.services.rag_service import RagService


QuestionType = Literal["conceptual", "implementation", "troubleshooting", "interview", "general"]


@dataclass
class AgentWorkflowState:
    request: AgentInvokeRequest
    question_type: QuestionType = "general"
    selected_strategy_name: str = "basic-rag"
    answer: str = ""
    citations: list = field(default_factory=list)
    follow_up_questions: list[str] = field(default_factory=list)
    rag_trace_id: str | None = None
    steps: list[AgentWorkflowStep] = field(default_factory=list)


class StudyAgentWorkflow:
    def __init__(self, *, rag_service: RagService) -> None:
        self.rag_service = rag_service

    async def run(self, *, payload: AgentInvokeRequest, trace_builder: TraceBuilder) -> AgentWorkflowState:
        state = AgentWorkflowState(request=payload)
        self._classify_question(state, trace_builder)
        self._select_rag_strategy(state, trace_builder)
        await self._retrieve_and_generate(state, trace_builder)
        self._cite_sources(state, trace_builder)
        self._generate_follow_up_questions(state, trace_builder)
        return state

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
        state.answer = rag_response.answer
        state.citations = rag_response.citations
        state.rag_trace_id = rag_response.trace.trace_id
        self._record_step(
            state,
            trace_builder,
            name="retrieve_and_generate",
            detail="Executed the selected RAG query path.",
            payload={
                "rag_trace_id": rag_response.trace.trace_id,
                "rag_run_id": rag_response.trace.run_id,
                "citation_count": len(rag_response.citations),
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

    def _generate_follow_up_questions(self, state: AgentWorkflowState, trace_builder: TraceBuilder) -> None:
        base_topic = _short_topic(state.request.user_input)
        if state.question_type == "interview":
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

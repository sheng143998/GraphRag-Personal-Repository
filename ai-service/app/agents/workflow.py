from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from app.core.tracing import TraceBuilder
from app.schemas.agent import AgentInvokeRequest, AgentWorkflowStep, ReviewCard, StudyPlan
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
    study_plan: StudyPlan | None = None
    review_cards: list[ReviewCard] = field(default_factory=list)
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
        self._generate_study_plan(state, trace_builder)
        self._generate_review_cards(state, trace_builder)
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

    def _generate_study_plan(self, state: AgentWorkflowState, trace_builder: TraceBuilder) -> None:
        base_topic = _short_topic(state.request.user_input)
        citation_focus = _citation_focus(state.citations)
        if state.question_type == "interview":
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
        if state.question_type == "interview":
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

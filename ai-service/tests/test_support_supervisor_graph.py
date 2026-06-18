import asyncio
import inspect
import os

import pytest

os.environ["AI_RAG_USE_DATABASE"] = "false"
os.environ["MODEL_PROVIDER"] = "stub"
os.environ["LLM_PROVIDER"] = "stub"
os.environ["EMBEDDING_PROVIDER"] = "stub"
os.environ["RERANK_PROVIDER"] = "stub"

from app.agents.graphs import support_supervisor
from app.core.constants import DocumentType, FileType
from app.core.tracing import TraceBuilder
from app.schemas.agent import AgentInvokeRequest
from app.schemas.ingest import DocumentIngestRequest, DocumentPayload
from app.schemas.rag import RagRequestContext
from app.services.adapters.registry import get_llm_model_name
from app.services.ingest_service import IngestService
from app.services.rag_service import RagService


def test_support_supervisor_local_runtime_clarification_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_AGENT_SUPPORT_WORKFLOW_RUNTIME", "local")

    state, trace = asyncio.run(_run_support_workflow("客户打不开系统。", knowledge_base_id="kb-supervisor-clarify"))

    assert state.workflow_runtime == "local"
    assert state.workflow_status == "needs_clarification"
    assert state.route.final_status == "needs_clarification"
    assert state.completed_gates == ["clarification_agent"]
    assert "retrieval_agent" in state.skipped_gates
    assert "risk_review_agent" in state.skipped_gates
    assert "evaluation_review_agent" in state.skipped_gates
    assert trace.attributes["workflow_requested_runtime"] == "local"
    assert trace.attributes["support_workflow_runtime_fallback_reason"] == "explicit_local_runtime"


def test_support_supervisor_completed_path_records_required_gate_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_AGENT_SUPPORT_WORKFLOW_RUNTIME", "local")

    state, _trace = asyncio.run(
        _run_support_workflow(
            (
                "客户 P1 大面积不可用，无法登录控制台，生产环境，"
                "日志显示 HTTP 504，trace_id=abc-123456。"
            ),
            knowledge_base_id="kb-supervisor-complete",
            variables={"mode": "technical-support", "product": "Support Console"},
            ingest_support_notes=True,
        )
    )

    assert state.workflow_runtime == "local"
    assert state.workflow_status == "completed"
    assert state.required_gates == [
        "clarification_agent",
        "retrieval_agent",
        "code_log_tool_agent",
        "diagnosis_agent",
        "risk_review_agent",
        "escalation_agent",
        "evaluation_review_agent",
    ]
    assert state.completed_gates == state.required_gates
    assert state.skipped_gates == []
    assert [step.name for step in state.workflow_steps][-1] == "support_supervisor_finish"


def test_support_supervisor_auto_runtime_falls_back_when_langgraph_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AI_AGENT_SUPPORT_WORKFLOW_RUNTIME", "auto")
    monkeypatch.setattr(support_supervisor, "_load_langgraph_runtime", lambda: None)

    state, trace = asyncio.run(
        _run_support_workflow(
            (
                "客户 P1 大面积不可用，无法登录控制台，生产环境，"
                "日志显示 HTTP 504，trace_id=abc-123456。"
            ),
            knowledge_base_id="kb-supervisor-auto-fallback",
            variables={"mode": "technical-support", "product": "Support Console"},
            ingest_support_notes=True,
        )
    )

    assert state.workflow_runtime == "local"
    assert trace.attributes["workflow_requested_runtime"] == "auto"
    assert trace.attributes["support_workflow_runtime_fallback_reason"] == "langgraph_dependency_unavailable"


def test_support_supervisor_auto_runtime_uses_state_graph_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("langchain_core.runnables")
    monkeypatch.setenv("AI_AGENT_SUPPORT_WORKFLOW_RUNTIME", "auto")
    monkeypatch.setattr(
        support_supervisor,
        "_load_langgraph_runtime",
        lambda: (_FakeStateGraph, "__start__", "__end__"),
    )

    state, trace = asyncio.run(
        _run_support_workflow(
            (
                "客户 P1 大面积不可用，无法登录控制台，生产环境，"
                "日志显示 HTTP 504，trace_id=abc-123456。"
            ),
            knowledge_base_id="kb-supervisor-langgraph",
            variables={"mode": "technical-support", "product": "Support Console"},
            ingest_support_notes=True,
        )
    )

    assert state.workflow_runtime == "langgraph"
    assert state.workflow_status == "completed"
    assert trace.attributes["workflow_requested_runtime"] == "auto"
    assert trace.attributes["workflow_runtime"] == "langgraph"
    assert "support_workflow_runtime_fallback_reason" not in trace.attributes
    assert state.required_gates == [
        "clarification_agent",
        "retrieval_agent",
        "code_log_tool_agent",
        "diagnosis_agent",
        "risk_review_agent",
        "escalation_agent",
        "evaluation_review_agent",
    ]
    assert state.completed_gates == state.required_gates
    assert state.skipped_gates == []
    assert [step.name for step in state.workflow_steps][:4] == [
        "support_supervisor_start",
        "clarification_agent",
        "retrieval_agent",
        "code_log_tool_agent",
    ]
    assert [step.name for step in state.workflow_steps][-1] == "support_supervisor_finish"


def test_support_supervisor_uses_real_langgraph_runtime_when_installed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    __import__("langgraph.graph")
    monkeypatch.setenv("AI_AGENT_SUPPORT_WORKFLOW_RUNTIME", "auto")

    state, trace = asyncio.run(
        _run_support_workflow(
            (
                "客户 P1 大面积不可用，无法登录控制台，生产环境，"
                "日志显示 HTTP 504，trace_id=abc-123456。"
            ),
            knowledge_base_id="kb-supervisor-real-langgraph",
            variables={"mode": "technical-support", "product": "Support Console"},
            ingest_support_notes=True,
        )
    )

    assert state.workflow_runtime == "langgraph"
    assert trace.attributes["workflow_runtime"] == "langgraph"
    assert state.workflow_status == "completed"
    assert state.completed_gates == state.required_gates
    assert [step.name for step in state.workflow_steps][-1] == "support_supervisor_finish"


def test_support_supervisor_explicit_langgraph_runtime_fails_when_dependency_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AI_AGENT_SUPPORT_WORKFLOW_RUNTIME", "langgraph")
    monkeypatch.setattr(support_supervisor, "_load_langgraph_runtime", lambda: None)

    with pytest.raises(RuntimeError, match="LangGraph runtime was requested"):
        asyncio.run(_run_support_workflow("客户打不开系统。", knowledge_base_id="kb-supervisor-langgraph-missing"))


def test_support_supervisor_auto_runtime_does_not_fallback_after_graph_execution_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("langchain_core.runnables")
    monkeypatch.setenv("AI_AGENT_SUPPORT_WORKFLOW_RUNTIME", "auto")
    monkeypatch.setattr(
        support_supervisor,
        "_load_langgraph_runtime",
        lambda: (_FailingExecutionStateGraph, "__start__", "__end__"),
    )

    with pytest.raises(RuntimeError, match="simulated graph execution failure"):
        asyncio.run(
            _run_support_workflow(
                (
                    "客户 P1 大面积不可用，无法登录控制台，生产环境，"
                    "日志显示 HTTP 504，trace_id=abc-123456。"
                ),
                knowledge_base_id="kb-supervisor-langgraph-execution-failure",
                variables={"mode": "technical-support", "product": "Support Console"},
                ingest_support_notes=True,
            )
        )


async def _run_support_workflow(
    question: str,
    *,
    knowledge_base_id: str,
    variables: dict[str, object] | None = None,
    ingest_support_notes: bool = False,
):
    if ingest_support_notes:
        await IngestService().ingest_document(
            DocumentIngestRequest(
                knowledge_base_id=knowledge_base_id,
                document_id=f"{knowledge_base_id}-doc",
                title="Support Supervisor Notes",
                document_type=DocumentType.TECH_NOTE,
                file=DocumentPayload(
                    filename="support-supervisor.md",
                    file_type=FileType.MARKDOWN,
                    content=(
                        "售后支持排障要求先确认客户影响范围、错误码、trace id 和业务影响，"
                        "再按 Runbook 执行安全检查；P1 或大面积不可用必须升级二线技术支持。"
                    ),
                ),
            )
        )
    workflow = support_supervisor.SupportSupervisorWorkflow(rag_service=RagService())
    trace_builder = TraceBuilder(
        operation="agent_invoke",
        strategy_name="basic-rag",
        prompt_name="agent_invoke",
        prompt_version="v1",
        model_name=get_llm_model_name(),
    )
    return await workflow.run(
        payload=AgentInvokeRequest(
            agent_name="technical-support-agent",
            user_input=question,
            strategy_name="basic-rag",
            top_k=3,
            context=RagRequestContext(knowledge_base_id=knowledge_base_id),
            variables=variables or {"mode": "technical-support"},
        ),
        trace_builder=trace_builder,
    ), trace_builder.trace


class _FakeStateGraph:
    def __init__(self, _state_schema):
        self.nodes: dict[str, object] = {}
        self.edges: dict[str, str] = {}
        self.conditional_edges: dict[str, tuple[object, dict[str, str]]] = {}

    def add_node(self, name: str, node) -> None:
        self.nodes[name] = node

    def add_edge(self, source: str, target: str) -> None:
        self.edges[source] = target

    def add_conditional_edges(self, source: str, condition, path_map: dict[str, str]) -> None:
        self.conditional_edges[source] = (condition, path_map)

    def compile(self):
        return _FakeCompiledGraph(self.nodes, self.edges, self.conditional_edges)


class _FakeCompiledGraph:
    def __init__(
        self,
        nodes: dict[str, object],
        edges: dict[str, str],
        conditional_edges: dict[str, tuple[object, dict[str, str]]],
    ) -> None:
        self.nodes = nodes
        self.edges = edges
        self.conditional_edges = conditional_edges

    async def ainvoke(self, graph_state):
        current = self.edges["__start__"]
        while current != "__end__":
            graph_state = await self._run_node(self.nodes[current], graph_state)
            if current in self.conditional_edges:
                condition, path_map = self.conditional_edges[current]
                route = condition(graph_state)
                current = path_map[route]
            else:
                current = self.edges[current]
        return graph_state

    async def _run_node(self, node, graph_state):
        if hasattr(node, "ainvoke"):
            return await node.ainvoke(graph_state)
        if hasattr(node, "invoke"):
            return node.invoke(graph_state)
        result = node(graph_state)
        if inspect.isawaitable(result):
            return await result
        return result


class _FailingExecutionStateGraph(_FakeStateGraph):
    def compile(self):
        return _FailingExecutionGraph(self.nodes, self.edges, self.conditional_edges)


class _FailingExecutionGraph(_FakeCompiledGraph):
    async def ainvoke(self, graph_state):
        current = self.edges["__start__"]
        graph_state = await self._run_node(self.nodes[current], graph_state)
        raise RuntimeError("simulated graph execution failure")

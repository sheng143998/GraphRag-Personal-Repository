import asyncio
import os

os.environ["AI_RAG_USE_DATABASE"] = "false"
os.environ["MODEL_PROVIDER"] = "stub"
os.environ["LLM_PROVIDER"] = "stub"
os.environ["EMBEDDING_PROVIDER"] = "stub"
os.environ["RERANK_PROVIDER"] = "stub"

from app.core.constants import DocumentType, FileType
from app.schemas.agent import AgentInvokeRequest
from app.schemas.ingest import DocumentIngestRequest, DocumentPayload
from app.schemas.rag import RagRequestContext
from app.services.agent_service import AgentService
from app.services.ingest_service import IngestService


def test_agent_workflow_routes_implementation_question_to_advanced_rag() -> None:
    response = asyncio.run(_invoke_agent("kb-agent-advanced", "How should I implement RAG rerank code?"))

    assert response.question_type == "implementation"
    assert response.selected_strategy_name == "advanced-rag"
    assert response.citations
    assert [step.name for step in response.workflow_steps] == [
        "classify_question",
        "select_rag_strategy",
        "retrieve_and_generate",
        "cite_sources",
        "generate_follow_up_questions",
        "generate_study_plan",
    ]
    assert len(response.follow_up_questions) == 3
    assert response.trace.attributes["follow_up_questions"] == response.follow_up_questions
    assert response.study_plan is not None
    assert len(response.study_plan.steps) == 3
    assert response.trace.attributes["study_plan"] == response.study_plan.dict()
    assert response.trace.attributes["question_type"] == "implementation"
    assert response.trace.attributes["selected_strategy_name"] == "advanced-rag"
    assert response.trace.attributes["rag_trace_id"]


def test_agent_workflow_respects_explicit_strategy() -> None:
    response = asyncio.run(
        _invoke_agent(
            "kb-agent-basic",
            "How does a basic RAG pipeline answer from context?",
            strategy_name="basic-rag",
        )
    )

    assert response.selected_strategy_name == "basic-rag"
    assert response.citations
    assert response.follow_up_questions
    assert response.study_plan is not None


async def _invoke_agent(
    knowledge_base_id: str,
    question: str,
    *,
    strategy_name: str = "basic-rag",
):
    ingest_service = IngestService()
    agent_service = AgentService()

    await ingest_service.ingest_document(
        DocumentIngestRequest(
            knowledge_base_id=knowledge_base_id,
            document_id=f"{knowledge_base_id}-doc",
            title="Agent Workflow Notes",
            document_type=DocumentType.TECH_NOTE,
            file=DocumentPayload(
                filename="agent-workflow.md",
                file_type=FileType.MARKDOWN,
                content=(
                    "Advanced RAG can rewrite implementation questions, retrieve multiple "
                    "candidate chunks, rerank them, and answer with citations. Basic RAG "
                    "retrieves context and generates an answer from the selected chunks."
                ),
            ),
        )
    )

    return await agent_service.invoke(
        AgentInvokeRequest(
            agent_name="study-agent",
            user_input=question,
            strategy_name=strategy_name,
            top_k=3,
            context=RagRequestContext(knowledge_base_id=knowledge_base_id),
        )
    )

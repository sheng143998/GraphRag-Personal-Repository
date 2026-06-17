import builtins
import json

import pytest

from app.rag.evaluators.ragas_bridge import (
    RagasUnavailableError,
    build_ragas_sample,
    evaluation_case_reference_context_ids,
    load_ragas_metrics,
    read_jsonl,
    write_jsonl,
)
from app.schemas.common import SourceMetadata
from app.schemas.rag import RagEvaluateRequest, RagEvaluationCase, RagRequestContext


def test_build_ragas_sample_maps_project_evaluation_payload() -> None:
    payload = RagEvaluateRequest(
        question="How should Advanced RAG cite evidence?",
        generated_answer="Use reranked citations with source chunks.",
        expected_answer="Advanced RAG should cite source chunks.",
        citations=[
            SourceMetadata(
                document_id="doc-a",
                chunk_id="required-a",
                title="Required Evidence",
                source_path="notes/rag.md",
                metadata={"content_preview": "Reranked citations should include source chunks."},
            ),
            SourceMetadata(
                document_id="doc-a",
                chunk_id="supporting-a",
                title="Supporting Evidence",
                metadata={"snippet": "Supporting context explains citation grounding."},
            ),
        ],
        strategy_name="advanced-rag",
        context=RagRequestContext(knowledge_base_id="kb-ragas"),
        evaluation_case=RagEvaluationCase(
            case_id="advanced-rag-citation",
            required_chunk_ids=["required-a"],
            supporting_chunk_ids=["supporting-a"],
            acceptable_chunk_ids=["acceptable-a"],
            relevant_chunk_ids=["legacy-a"],
            citation_chunk_ids=["required-a"],
            expected_citation_chunk_ids=["supporting-a"],
            top_k=2,
        ),
    )

    sample = build_ragas_sample(payload)

    assert sample == {
        "user_input": "How should Advanced RAG cite evidence?",
        "response": "Use reranked citations with source chunks.",
        "reference": "Advanced RAG should cite source chunks.",
        "retrieved_contexts": [
            "Reranked citations should include source chunks.",
            "Supporting context explains citation grounding.",
        ],
        "retrieved_context_ids": ["required-a", "supporting-a"],
        "reference_context_ids": ["required-a", "supporting-a", "acceptable-a", "legacy-a"],
        "metadata": {
            "case_id": "advanced-rag-citation",
            "strategy_name": "advanced-rag",
            "knowledge_base_id": "kb-ragas",
            "top_k": 2,
        },
    }


def test_evaluation_case_reference_context_ids_deduplicates_in_label_order() -> None:
    case = RagEvaluationCase(
        case_id="layered",
        required_chunk_ids=["a", "b"],
        supporting_chunk_ids=["b", "c"],
        acceptable_chunk_ids=["d"],
        relevant_chunk_ids=["a", "legacy"],
        citation_chunk_ids=["c"],
        expected_citation_chunk_ids=["e"],
    )

    assert evaluation_case_reference_context_ids(case) == ["a", "b", "c", "d", "legacy", "e"]


def test_ragas_jsonl_round_trip(tmp_path) -> None:
    output = tmp_path / "ragas.jsonl"
    rows = [
        {"user_input": "q1", "retrieved_contexts": ["c1"]},
        {"user_input": "q2", "retrieved_context_ids": ["chunk-2"]},
    ]

    write_jsonl(rows, output)

    assert output.read_text(encoding="utf-8").count("\n") == 2
    assert read_jsonl(output) == rows


def test_load_ragas_metrics_reports_optional_dependency_when_missing(monkeypatch) -> None:
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "ragas":
            raise ImportError("missing ragas")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(RagasUnavailableError, match="pydantic>=2"):
        load_ragas_metrics(["IDBasedContextRecall"])


def test_jsonl_output_is_utf8_and_not_ascii_escaped(tmp_path) -> None:
    output = tmp_path / "ragas-cn.jsonl"
    write_jsonl([{"user_input": "什么是 RAG？"}], output)

    line = output.read_text(encoding="utf-8").strip()
    assert "什么是 RAG" in line
    assert json.loads(line)["user_input"] == "什么是 RAG？"

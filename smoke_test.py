#!/usr/bin/env python3
"""Full-chain HTTP smoke test for the Knowledge Base Workbench."""

import requests
import os
import sys
import time
import uuid
from datetime import datetime, timezone

BASE = os.getenv("SMOKE_BASE_URL", "http://localhost:8080/api").rstrip("/")
AI_BASE = os.getenv("SMOKE_AI_BASE_URL", "http://localhost:8001/ai").rstrip("/")
TIMEOUT = int(os.getenv("SMOKE_TIMEOUT", "15"))
PASS = 0
FAIL = 0
ERRORS = []

CREATED_KB_ID = None
CREATED_DOC_ID = None
CREATED_PARENT_DOC_ID = None
PARENT_CHILD_DOC_INDEXED = False
CREATED_SESSION_ID = None
CREATED_EXP_ID = None
CREATED_MSG_ID = None
CREATED_ASSISTANT_MSG_ID = None
CREATED_RUN_ID = None
CREATED_ADVANCED_RUN_ID = None
CREATED_PARENT_CHILD_RUN_ID = None
ADVANCED_EVALUATION_CASE = None
CREATED_AGENT_RUN_ID = None
CREATED_GRAPH_RUN_ID = None
TEST_UUID = str(uuid.uuid4())  # for use as placeholder UUIDs


def do(method, url, **kw):
    kw.setdefault("timeout", TIMEOUT)
    try:
        r = requests.request(method, url, **kw)
    except Exception as e:
        return None, f"EXCEPTION: {type(e).__name__}: {e}"
    try:
        body = r.json()
    except Exception:
        body = r.text[:300]
    return r, body


def check(label, method, url, **kw):
    global PASS, FAIL
    expect_status = kw.pop("expect", 200)
    r, body = do(method, url, **kw)
    status = r.status_code if r is not None else -1
    ok = status == expect_status if isinstance(expect_status, int) else status in expect_status
    if ok:
        PASS += 1
        print(f"  PASS  [{status}] {label}")
    else:
        FAIL += 1
        msg = str(body)[:200]
        ERRORS.append(f"{label}: expected {expect_status}, got {status} body={msg}")
        print(f"  FAIL  [{status}] {label}  (expected {expect_status})  {msg}")
    return r, body


def check_field(label, body, field, expected=None):
    global PASS, FAIL
    val = body
    for seg in field.split("."):
        if isinstance(val, dict):
            val = val.get(seg)
        else:
            val = None
            break
    if expected is not None:
        if val == expected:
            PASS += 1
            print(f"  PASS  {label}: {field} = {val}")
        else:
            FAIL += 1
            ERRORS.append(f"{label}: {field} expected={expected}, got={val}")
            print(f"  FAIL  {label}: {field} expected={expected}, got={val}")
    else:
        if val is not None:
            PASS += 1
            print(f"  PASS  {label}: {field} present = {str(val)[:80]}")
        else:
            FAIL += 1
            ERRORS.append(f"{label}: {field} is None")
            print(f"  FAIL  {label}: {field} is None")
    return val


def check_datetime_after_now(label, value):
    global PASS, FAIL
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception as exc:
        FAIL += 1
        ERRORS.append(f"{label}: could not parse datetime {value!r}: {exc}")
        print(f"  FAIL  {label}: invalid datetime {value!r}")
        return
    if parsed > datetime.now(timezone.utc):
        PASS += 1
        print(f"  PASS  {label}: {parsed.isoformat()} is in the future")
    else:
        FAIL += 1
        ERRORS.append(f"{label}: expected future datetime, got {parsed.isoformat()}")
        print(f"  FAIL  {label}: expected future datetime, got {parsed.isoformat()}")


def wait_for_document_index(document_id, attempts=60, delay=0.5):
    for _ in range(attempts):
        r, body = do("GET", f"{BASE}/documents/{document_id}")
        if r is not None and r.status_code == 200:
            status = body.get("data", {}).get("status") if isinstance(body, dict) else None
            if status in {"INDEXED", "FAILED"}:
                return r, body
        time.sleep(delay)
    return do("GET", f"{BASE}/documents/{document_id}")


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ============================================================
section("1. HEALTH CHECK")
# ============================================================

r, body = check("Spring Boot health", "GET", f"{BASE}/health")
if r is not None and r.status_code == 200:
    check_field("SB health", body, "data.status", "UP")

r2, body2 = check("FastAPI health", "GET", f"{AI_BASE}/health")
if r2 and r2.status_code == 200:
    check_field("FastAPI health", body2, "status", "ok")


# ============================================================
section("2. KNOWLEDGE BASES CRUD")
# ============================================================

r, body = check("List KBs", "GET", f"{BASE}/knowledge-bases")

r, body = check("Create KB", "POST", f"{BASE}/knowledge-bases",
                json={"name": f"smoke-kb-{uuid.uuid4().hex[:6]}",
                       "description": "Smoke test KB",
                       "embeddingModel": "text-embedding-v3",
                       "chunkSize": 512,
                       "chunkOverlap": 50})
if r is not None and r.status_code == 200:
    CREATED_KB_ID = check_field("KB id", body, "data.id")

if CREATED_KB_ID:
    r, body = check("Get KB detail", "GET", f"{BASE}/knowledge-bases/{CREATED_KB_ID}")
    if r is not None and r.status_code == 200:
        check_field("KB detail", body, "data.name")

    r, body = check("Update KB", "PUT", f"{BASE}/knowledge-bases/{CREATED_KB_ID}",
                    json={"name": f"smoke-kb-upd-{uuid.uuid4().hex[:4]}",
                          "description": "Updated KB",
                          "embeddingModel": "text-embedding-v3",
                          "chunkSize": 1024,
                          "chunkOverlap": 100})
    if r is not None and r.status_code == 200:
        check_field("KB updated", body, "data.name")

check("List KBs after create", "GET", f"{BASE}/knowledge-bases")


# ============================================================
section("3. DOCUMENTS UPLOAD / LIST / DETAIL")
# ============================================================

if CREATED_KB_ID:
    test_content = (
        "This is a smoke test document.\n"
        "GraphRAG uses entities and relationships to enhance Advanced RAG retrieval.\n"
        "Entity extraction links GraphRAG, RAG, Knowledge Graph, and Rerank signals."
    )
    files = {"file": ("smoke-test.txt", test_content.encode("utf-8"), "text/plain")}
    data = {
        "knowledgeBaseId": CREATED_KB_ID,
        "title": f"Smoke Test Doc {uuid.uuid4().hex[:4]}",
        "documentType": "tech_note",
    }
    r, body = check("Upload document", "POST", f"{BASE}/documents/upload",
                    data=data, files=files)
    if r is not None and r.status_code == 200:
        CREATED_DOC_ID = check_field("Doc id", body, "data.id")

    check("List documents", "GET", f"{BASE}/documents",
          params={"knowledgeBaseId": CREATED_KB_ID})

    if CREATED_DOC_ID:
        check("Get doc detail", "GET", f"{BASE}/documents/{CREATED_DOC_ID}")

    parent_child_content = (
        "Parent child retrieval improves Advanced RAG context by storing a broad parent passage. "
        "The child chunk carries precise rerank scoring details and points back to the parent passage. "
        "Parent context helps citations explain query rewrite, retrieval, and rerank decisions together. "
        * 8
    )
    parent_document_id = str(uuid.uuid4())
    r, body = check("Ingest parent-child document", "POST", f"{AI_BASE}/ingest/document",
                    json={
                        "knowledge_base_id": CREATED_KB_ID,
                        "document_id": parent_document_id,
                        "title": f"Parent Child Doc {uuid.uuid4().hex[:4]}",
                        "document_type": "tech_note",
                        "file": {
                            "filename": "parent-child.md",
                            "file_type": "md",
                            "content": parent_child_content,
                            "mime_type": "text/markdown"
                        },
                        "metadata": {
                            "topic": "parent-child",
                            "chunk_strategy": "parent-child",
                            "parent_chunk_size": 900,
                            "child_chunk_size": 300
                        }
                    })
    if r is not None and r.status_code == 200:
        CREATED_PARENT_DOC_ID = check_field("Parent-child doc id", body, "document_id", parent_document_id)
        PARENT_CHILD_DOC_INDEXED = True
        chunk_count = body.get("chunk_count") if isinstance(body, dict) else None
        if isinstance(chunk_count, int) and chunk_count >= 3:
            PASS += 1
            print(f"  PASS  Parent-child chunk count = {chunk_count}")
        else:
            FAIL += 1
            ERRORS.append(f"Parent-child chunk count expected >= 3, got {chunk_count}")
            print(f"  FAIL  Parent-child chunk count expected >= 3, got {chunk_count}")
else:
    print("  SKIP  No KB, skipping document tests")


# ============================================================
section("4. RAG QUERY + RUNS + EXPERIMENTS")
# ============================================================

rag_kb_id = CREATED_KB_ID or "00000000-0000-0000-0000-000000000001"
print(f"  INFO  RAG query with KB={rag_kb_id}")
r, body = check("RAG query", "POST", f"{BASE}/rag/query",
                json={"question": "What is machine learning?",
                      "knowledgeBaseId": rag_kb_id,
                      "topK": 3})
if r is not None and r.status_code == 200:
    CREATED_RUN_ID = check_field("RAG runId", body, "data.runId")

# Experiments CRUD
check("List experiments", "GET", f"{BASE}/rag/experiments")

r, body = check("Create experiment", "POST", f"{BASE}/rag/experiments",
                json={"name": f"smoke-exp-{uuid.uuid4().hex[:6]}",
                       "description": "Smoke test experiment",
                       "strategy": "naive_rag",
                       "datasetName": "smoke-dataset",
                       "sampleCount": 10,
                       "status": "PLANNED"})
if r is not None and r.status_code == 200:
    CREATED_EXP_ID = check_field("Exp id", body, "data.id")

if CREATED_EXP_ID:
    check("Get exp detail", "GET", f"{BASE}/rag/experiments/{CREATED_EXP_ID}")
    check("Update exp", "PUT", f"{BASE}/rag/experiments/{CREATED_EXP_ID}",
          json={"name": f"smoke-exp-upd-{uuid.uuid4().hex[:4]}",
                "description": "Updated experiment",
                "strategy": "naive_rag",
                "datasetName": "smoke-dataset-v2",
                "sampleCount": 20,
                "status": "RUNNING"})

if CREATED_RUN_ID:
    check("Get RAG run", "GET", f"{BASE}/rag/runs/{CREATED_RUN_ID}")
    r, body = check("List recent RAG runs", "GET", f"{BASE}/rag/runs?limit=10")
    if r is not None and r.status_code == 200:
        runs = body.get("data") if isinstance(body, dict) else None
        if isinstance(runs, list) and any(isinstance(run, dict) and run.get("id") == CREATED_RUN_ID for run in runs):
            PASS += 1
            print("  PASS  Recent RAG runs include created run")
        else:
            FAIL += 1
            ERRORS.append("Recent RAG runs expected to include created run")
            print("  FAIL  Recent RAG runs expected to include created run")


# ============================================================
section("4B. ADVANCED RAG HTTP TRACE")
# ============================================================

if CREATED_KB_ID:
    r, body = check("Advanced RAG query", "POST", f"{BASE}/rag/query",
                    json={"question": "How does advanced RAG use metadata filters and rerank?",
                          "knowledgeBaseId": CREATED_KB_ID,
                          "topK": 3,
                          "strategyName": "advanced-rag",
                          "metadataFilters": {},
                          "retrievalOptions": {"vectorWeight": 0.6, "keywordWeight": 0.4}})
    if r is not None and r.status_code == 200:
        CREATED_ADVANCED_RUN_ID = check_field("Advanced RAG runId", body, "data.runId")
        check_field("Advanced RAG status", body, "data.status", "COMPLETED")
        check_field("Advanced RAG strategy", body, "data.strategyName", "advanced-rag")
        citations = body.get("data", {}).get("citations") if isinstance(body, dict) else None
        if citations:
            PASS += 1
            print(f"  PASS  Advanced RAG citations present = {len(citations)}")
        else:
            FAIL += 1
            ERRORS.append("Advanced RAG citations expected at least one result")
            print("  FAIL  Advanced RAG citations expected at least one result")

    if CREATED_ADVANCED_RUN_ID:
        r, body = check("Get Advanced RAG run", "GET", f"{BASE}/rag/runs/{CREATED_ADVANCED_RUN_ID}")
        if r is not None and r.status_code == 200:
            check_field("Advanced RAG run status", body, "data.status", "COMPLETED")
            check_field("Advanced RAG rewritten query", body, "data.rewrittenQuery")
            retrieval_results = body.get("data", {}).get("retrievalResults") if isinstance(body, dict) else None
            first_result = retrieval_results[0] if isinstance(retrieval_results, list) and retrieval_results else None
            if isinstance(first_result, dict) and first_result.get("chunkId"):
                first_metadata = first_result.get("metadata") if isinstance(first_result.get("metadata"), dict) else {}
                if first_metadata.get("vector_weight") == 0.6 and first_metadata.get("keyword_weight") == 0.4:
                    PASS += 1
                    print("  PASS  Advanced RAG hybrid weights persisted in retrieval metadata")
                else:
                    FAIL += 1
                    ERRORS.append(
                        f"Advanced RAG hybrid weights expected 0.6/0.4, got {first_metadata.get('vector_weight')}/{first_metadata.get('keyword_weight')}"
                    )
                    print(
                        f"  FAIL  Advanced RAG hybrid weights expected 0.6/0.4, got {first_metadata.get('vector_weight')}/{first_metadata.get('keyword_weight')}"
                    )
                ADVANCED_EVALUATION_CASE = {
                    "evaluationCaseId": "smoke-advanced-rag",
                    "relevantChunkIds": [first_result.get("chunkId")],
                    "expectedCitationChunkIds": [first_result.get("chunkId")],
                    "evaluationTopK": 1,
                }
                if first_result.get("documentId"):
                    ADVANCED_EVALUATION_CASE["relevantDocumentIds"] = [first_result.get("documentId")]
        if CREATED_EXP_ID:
            advanced_eval_payload = {
                "runId": CREATED_ADVANCED_RUN_ID,
                "expectedAnswer": "Advanced RAG should use metadata filters and rerank evidence.",
            }
            if ADVANCED_EVALUATION_CASE:
                advanced_eval_payload.update(ADVANCED_EVALUATION_CASE)
            r, body = check("Evaluate experiment from Advanced RAG run", "POST",
                            f"{BASE}/rag/experiments/{CREATED_EXP_ID}/evaluate",
                            json=advanced_eval_payload)
            if r is not None and r.status_code == 200:
                check_field("Experiment evaluation status", body, "data.experiment.status", "COMPLETED")
                check_field("Experiment grounded score", body, "data.groundedScore")
                check_field("Experiment retrieval score", body, "data.retrievalScore")
                check_field("Experiment evaluation run", body, "data.evaluation.runId", CREATED_ADVANCED_RUN_ID)
                notes = body.get("data", {}).get("notes") if isinstance(body, dict) else None
                if isinstance(notes, list) and notes:
                    PASS += 1
                    print(f"  PASS  Experiment evaluation notes present = {len(notes)}")
                else:
                    FAIL += 1
                    ERRORS.append("Experiment evaluation expected non-empty notes")
                    print("  FAIL  Experiment evaluation expected non-empty notes")
                if ADVANCED_EVALUATION_CASE and any("Structured evaluation case scored" in str(note) for note in notes or []):
                    PASS += 1
                    print("  PASS  Experiment evaluation used structured retrieval metrics")
                elif ADVANCED_EVALUATION_CASE:
                    FAIL += 1
                    ERRORS.append("Experiment evaluation expected structured retrieval metrics note")
                    print("  FAIL  Experiment evaluation expected structured retrieval metrics note")
                history = body.get("data", {}).get("history") if isinstance(body, dict) else None
                experiment_history = body.get("data", {}).get("experiment", {}).get("evaluations") if isinstance(body, dict) else None
                if isinstance(history, list) and any(item.get("runId") == CREATED_ADVANCED_RUN_ID for item in history if isinstance(item, dict)):
                    PASS += 1
                    print(f"  PASS  Experiment evaluation history includes run = {CREATED_ADVANCED_RUN_ID}")
                else:
                    FAIL += 1
                    ERRORS.append("Experiment evaluation history expected evaluated run")
                    print("  FAIL  Experiment evaluation history expected evaluated run")
                latest_history = history[0] if isinstance(history, list) and history and isinstance(history[0], dict) else None
                if latest_history and latest_history.get("runQuestion") and latest_history.get("runStrategyName"):
                    PASS += 1
                    print("  PASS  Experiment history includes run question and strategy")
                else:
                    FAIL += 1
                    ERRORS.append("Experiment history expected runQuestion and runStrategyName")
                    print("  FAIL  Experiment history expected runQuestion and runStrategyName")
                if latest_history and latest_history.get("runLatencyMs") is not None:
                    PASS += 1
                    print(f"  PASS  Experiment history includes run latency = {latest_history.get('runLatencyMs')}ms")
                else:
                    FAIL += 1
                    ERRORS.append("Experiment history expected runLatencyMs")
                    print("  FAIL  Experiment history expected runLatencyMs")
                if isinstance(experiment_history, list) and experiment_history:
                    PASS += 1
                    print(f"  PASS  Experiment response evaluations present = {len(experiment_history)}")
                else:
                    FAIL += 1
                    ERRORS.append("Experiment response expected evaluations history")
                    print("  FAIL  Experiment response expected evaluations history")
                if CREATED_RUN_ID:
                    r, body = check("Evaluate experiment from Basic RAG run", "POST",
                                    f"{BASE}/rag/experiments/{CREATED_EXP_ID}/evaluate",
                                    json={"runId": CREATED_RUN_ID,
                                          "expectedAnswer": "Basic RAG should answer from the smoke document."})
                    if r is not None and r.status_code == 200:
                        second_history = body.get("data", {}).get("history") if isinstance(body, dict) else None
                        if isinstance(second_history, list) and len(second_history) >= 2:
                            PASS += 1
                            print(f"  PASS  Experiment evaluation comparison history present = {len(second_history)}")
                        else:
                            FAIL += 1
                            ERRORS.append("Experiment evaluation comparison expected at least two history rows")
                            print("  FAIL  Experiment evaluation comparison expected at least two history rows")
                        r, body = check("Experiment evaluation summary", "GET",
                                        f"{BASE}/rag/experiment-evaluations/summary?limit=10")
                        if r is not None and r.status_code == 200:
                            check_field("Experiment summary count", body, "data.evaluationCount")
                            check_field("Experiment summary average grounded", body, "data.averageGrounded")
                            check_field("Experiment summary average retrieval", body, "data.averageRetrieval")
                            summary_recent = body.get("data", {}).get("recentEvaluations") if isinstance(body, dict) else None
                            if isinstance(summary_recent, list) and len(summary_recent) >= 2:
                                PASS += 1
                                print(f"  PASS  Experiment summary recent evaluations present = {len(summary_recent)}")
                            else:
                                FAIL += 1
                                ERRORS.append("Experiment summary expected at least two recent evaluations")
                                print("  FAIL  Experiment summary expected at least two recent evaluations")
                            first_summary = (
                                summary_recent[0]
                                if isinstance(summary_recent, list) and summary_recent and isinstance(summary_recent[0], dict)
                                else None
                            )
                            if first_summary and first_summary.get("experimentName") and first_summary.get("runQuestion"):
                                PASS += 1
                                print("  PASS  Experiment summary includes experiment and run context")
                            else:
                                FAIL += 1
                                ERRORS.append("Experiment summary expected experimentName and runQuestion")
                                print("  FAIL  Experiment summary expected experimentName and runQuestion")
                            check_field("Experiment summary best experiment", body, "data.bestExperimentName")
else:
    print("  SKIP  No KB, skipping advanced RAG trace test")


# ============================================================
section("4B2. PARENT-CHILD INGEST TRACE")
# ============================================================

if CREATED_KB_ID and CREATED_PARENT_DOC_ID and PARENT_CHILD_DOC_INDEXED:
    r, body = check("Parent-child RAG query", "POST", f"{BASE}/rag/query",
                    json={"question": "How does parent child retrieval improve Advanced RAG context?",
                          "knowledgeBaseId": CREATED_KB_ID,
                          "topK": 2,
                          "strategyName": "parent-child",
                          "metadataFilters": {"topic": "parent-child"}})
    if r is not None and r.status_code == 200:
        CREATED_PARENT_CHILD_RUN_ID = check_field("Parent-child RAG runId", body, "data.runId")
        check_field("Parent-child RAG status", body, "data.status", "COMPLETED")
        check_field("Parent-child RAG strategy", body, "data.strategyName", "parent-child")

    if CREATED_PARENT_CHILD_RUN_ID:
        r, body = check("Get Parent-child RAG run", "GET", f"{BASE}/rag/runs/{CREATED_PARENT_CHILD_RUN_ID}")
        if r is not None and r.status_code == 200:
            retrieval_results = body.get("data", {}).get("retrievalResults") if isinstance(body, dict) else None
            parent_child_metadata = (
                retrieval_results[0].get("metadata", {})
                if isinstance(retrieval_results, list) and retrieval_results and isinstance(retrieval_results[0], dict)
                else {}
            )
            if parent_child_metadata.get("parent_child_mode") == "parent-child":
                PASS += 1
                print("  PASS  Parent-child run used real parent context")
            else:
                FAIL += 1
                ERRORS.append(f"Parent-child run expected parent_child_mode=parent-child, got {parent_child_metadata.get('parent_child_mode')}")
                print(f"  FAIL  Parent-child run expected parent_child_mode=parent-child, got {parent_child_metadata.get('parent_child_mode')}")
            if parent_child_metadata.get("parent_chunk_id"):
                PASS += 1
                print(f"  PASS  Parent-child run parent chunk id present = {parent_child_metadata.get('parent_chunk_id')}")
            else:
                FAIL += 1
                ERRORS.append("Parent-child run expected parent_chunk_id metadata")
                print("  FAIL  Parent-child run expected parent_chunk_id metadata")
else:
    print("  SKIP  No parent-child document, skipping parent-child trace")


# ============================================================
section("4C. AGENT WORKFLOW")
# ============================================================

if CREATED_KB_ID:
    r, body = check("Agent invoke", "POST", f"{BASE}/agent/invoke",
                    json={"agentName": "study-agent",
                          "userInput": "How should I implement advanced RAG rerank code?",
                          "knowledgeBaseId": CREATED_KB_ID,
                          "topK": 3})
    if r is not None and r.status_code == 200:
        check_field("Agent output", body, "data.output")
        check_field("Agent question type", body, "data.questionType", "implementation")
        check_field("Agent selected strategy", body, "data.selectedStrategyName", "advanced-rag")
        steps = body.get("data", {}).get("workflowSteps") if isinstance(body, dict) else None
        if steps and len(steps) >= 4:
            PASS += 1
            print(f"  PASS  Agent workflow steps present = {len(steps)}")
        else:
            FAIL += 1
            ERRORS.append("Agent workflow expected at least four workflow steps")
            print("  FAIL  Agent workflow expected at least four workflow steps")
        step_names = [step.get("name") for step in steps if isinstance(step, dict)] if steps else []
        if "generate_follow_up_questions" in step_names:
            PASS += 1
            print("  PASS  Agent workflow follow-up step present")
        else:
            FAIL += 1
            ERRORS.append("Agent workflow expected generate_follow_up_questions step")
            print("  FAIL  Agent workflow expected generate_follow_up_questions step")
        follow_up_questions = body.get("data", {}).get("followUpQuestions") if isinstance(body, dict) else None
        if (
            isinstance(follow_up_questions, list)
            and len(follow_up_questions) >= 3
            and all(isinstance(item, str) and item.strip() for item in follow_up_questions)
        ):
            PASS += 1
            print(f"  PASS  Agent follow-up questions present = {len(follow_up_questions)}")
        else:
            FAIL += 1
            ERRORS.append("Agent invoke expected at least three follow-up questions")
            print("  FAIL  Agent invoke expected at least three follow-up questions")
        trace_follow_ups = (
            body.get("data", {}).get("trace", {}).get("attributes", {}).get("follow_up_questions")
            if isinstance(body, dict)
            else None
        )
        if trace_follow_ups == follow_up_questions:
            PASS += 1
            print("  PASS  Agent trace follow-up questions match response")
        else:
            FAIL += 1
            ERRORS.append("Agent trace follow_up_questions expected to match response followUpQuestions")
            print("  FAIL  Agent trace follow_up_questions expected to match response followUpQuestions")
        study_plan = body.get("data", {}).get("studyPlan") if isinstance(body, dict) else None
        study_steps = study_plan.get("steps") if isinstance(study_plan, dict) else None
        if isinstance(study_steps, list) and len(study_steps) >= 3:
            PASS += 1
            print(f"  PASS  Agent study plan steps present = {len(study_steps)}")
        else:
            FAIL += 1
            ERRORS.append("Agent invoke expected at least three study plan steps")
            print("  FAIL  Agent invoke expected at least three study plan steps")
        trace_study_plan = (
            body.get("data", {}).get("trace", {}).get("attributes", {}).get("study_plan")
            if isinstance(body, dict)
            else None
        )
        if (
            isinstance(trace_study_plan, dict)
            and isinstance(study_plan, dict)
            and trace_study_plan.get("summary") == study_plan.get("summary")
            and trace_study_plan.get("steps") == study_plan.get("steps")
        ):
            PASS += 1
            print("  PASS  Agent trace study plan matches response")
        else:
            FAIL += 1
            ERRORS.append("Agent trace study_plan expected matching summary and steps")
            print("  FAIL  Agent trace study_plan expected matching summary and steps")
        review_cards = body.get("data", {}).get("reviewCards") if isinstance(body, dict) else None
        if isinstance(review_cards, list) and len(review_cards) >= 2:
            PASS += 1
            print(f"  PASS  Agent review cards present = {len(review_cards)}")
        else:
            FAIL += 1
            ERRORS.append("Agent invoke expected at least two review cards")
            print("  FAIL  Agent invoke expected at least two review cards")
        trace_review_cards = (
            body.get("data", {}).get("trace", {}).get("attributes", {}).get("review_cards")
            if isinstance(body, dict)
            else None
        )
        response_card_questions = [card.get("question") for card in review_cards if isinstance(card, dict)] if review_cards else []
        trace_card_questions = [card.get("question") for card in trace_review_cards if isinstance(card, dict)] if trace_review_cards else []
        if trace_card_questions == response_card_questions:
            PASS += 1
            print("  PASS  Agent trace review cards match response questions")
        else:
            FAIL += 1
            ERRORS.append("Agent trace review_cards expected matching response questions")
            print("  FAIL  Agent trace review_cards expected matching response questions")
else:
    print("  SKIP  No KB, skipping agent workflow test")


# ============================================================
section("4D. GRAPH RAG TRACE")
# ============================================================

if CREATED_KB_ID:
    r, body = check("GraphRAG query", "POST", f"{BASE}/rag/query",
                    json={"question": "How does GraphRAG use entities and relationships?",
                          "knowledgeBaseId": CREATED_KB_ID,
                          "topK": 3,
                          "strategyName": "graph-rag",
                          "metadataFilters": {}})
    if r is not None and r.status_code == 200:
        CREATED_GRAPH_RUN_ID = check_field("GraphRAG runId", body, "data.runId")
        check_field("GraphRAG status", body, "data.status", "COMPLETED")
        check_field("GraphRAG strategy", body, "data.strategyName", "graph-rag")
        citations = body.get("data", {}).get("citations") if isinstance(body, dict) else None
        if citations:
            PASS += 1
            print(f"  PASS  GraphRAG citations present = {len(citations)}")
        else:
            FAIL += 1
            ERRORS.append("GraphRAG citations expected at least one result")
            print("  FAIL  GraphRAG citations expected at least one result")

    if CREATED_GRAPH_RUN_ID:
        r, body = check("Get GraphRAG run", "GET", f"{BASE}/rag/runs/{CREATED_GRAPH_RUN_ID}")
        if r is not None and r.status_code == 200:
            check_field("GraphRAG run status", body, "data.status", "COMPLETED")
            retrieval_results = body.get("data", {}).get("retrievalResults") if isinstance(body, dict) else None
            graph_metadata = (
                retrieval_results[0].get("metadata", {})
                if retrieval_results and isinstance(retrieval_results[0], dict)
                else {}
            )
            if graph_metadata.get("graph_expansion_terms"):
                PASS += 1
                print(f"  PASS  GraphRAG expansion terms present = {len(graph_metadata.get('graph_expansion_terms'))}")
            else:
                FAIL += 1
                ERRORS.append("GraphRAG run metadata expected graph_expansion_terms")
                print("  FAIL  GraphRAG run metadata expected graph_expansion_terms")
            if graph_metadata.get("graph_traversal_relationships"):
                PASS += 1
                print(f"  PASS  GraphRAG traversal relationships present = {len(graph_metadata.get('graph_traversal_relationships'))}")
            else:
                FAIL += 1
                ERRORS.append("GraphRAG run metadata expected graph_traversal_relationships")
                print("  FAIL  GraphRAG run metadata expected graph_traversal_relationships")
else:
    print("  SKIP  No KB, skipping GraphRAG trace test")


# ============================================================
section("4E. GRAPH FACTS QUERY")
# ============================================================

if CREATED_KB_ID:
    r, body = check("Get graph facts", "GET", f"{BASE}/graph/facts",
                    params={"knowledgeBaseId": CREATED_KB_ID})
    if r is not None and r.status_code == 200:
        check_field("Graph facts entity count", body, "data.entityCount")
        check_field("Graph facts relationship count", body, "data.relationshipCount")
        entities = body.get("data", {}).get("entities") if isinstance(body, dict) else None
        relationships = body.get("data", {}).get("relationships") if isinstance(body, dict) else None
        if entities:
            PASS += 1
            print(f"  PASS  Graph facts entities present = {len(entities)}")
        else:
            FAIL += 1
            ERRORS.append("Graph facts expected at least one entity")
            print("  FAIL  Graph facts expected at least one entity")
        if relationships:
            PASS += 1
            print(f"  PASS  Graph facts relationships present = {len(relationships)}")
        else:
            FAIL += 1
            ERRORS.append("Graph facts expected at least one relationship")
            print("  FAIL  Graph facts expected at least one relationship")

    check("Get graph facts filtered", "GET", f"{BASE}/graph/facts",
          params={"knowledgeBaseId": CREATED_KB_ID, "entity": "GraphRAG"})
else:
    print("  SKIP  No KB, skipping graph facts query test")


# ============================================================
section("5. CHAT SESSIONS + MESSAGES")
# ============================================================

r, body = check("Create session", "POST", f"{BASE}/chat/sessions",
                json={"knowledgeBaseId": CREATED_KB_ID or "00000000-0000-0000-0000-000000000001",
                       "title": f"smoke-session-{uuid.uuid4().hex[:6]}"})
if r is not None and r.status_code == 200:
    CREATED_SESSION_ID = check_field("Session id", body, "data.id")

check("List sessions", "GET", f"{BASE}/chat/sessions")

if CREATED_SESSION_ID:
    r, body = check("Assistant turn", "POST", f"{BASE}/chat/{CREATED_SESSION_ID}/assistant-turn",
                    json={"userInput": "Give me an interview-ready answer about GraphRAG traversal.",
                          "topK": 3,
                          "metadataFilters": {}})
    if r is not None and r.status_code == 200:
        check_field("Assistant turn user message", body, "data.userMessage.id")
        CREATED_ASSISTANT_MSG_ID = check_field("Assistant turn assistant message", body, "data.assistantMessage.id")
        check_field("Assistant turn question type", body, "data.questionType")
        check_field("Assistant turn strategy", body, "data.selectedStrategyName")
        workflow_steps = body.get("data", {}).get("workflowSteps") if isinstance(body, dict) else None
        if workflow_steps and len(workflow_steps) >= 4:
            PASS += 1
            print(f"  PASS  Assistant turn workflow steps present = {len(workflow_steps)}")
        else:
            FAIL += 1
            ERRORS.append("Assistant turn expected at least four workflow steps")
            print("  FAIL  Assistant turn expected at least four workflow steps")
        assistant_step_names = (
            [step.get("name") for step in workflow_steps if isinstance(step, dict)]
            if workflow_steps
            else []
        )
        if "generate_follow_up_questions" in assistant_step_names:
            PASS += 1
            print("  PASS  Assistant turn follow-up step present")
        else:
            FAIL += 1
            ERRORS.append("Assistant turn expected generate_follow_up_questions step")
            print("  FAIL  Assistant turn expected generate_follow_up_questions step")
        follow_up_questions = body.get("data", {}).get("followUpQuestions") if isinstance(body, dict) else None
        if (
            isinstance(follow_up_questions, list)
            and len(follow_up_questions) >= 3
            and all(isinstance(item, str) and item.strip() for item in follow_up_questions)
        ):
            PASS += 1
            print(f"  PASS  Assistant turn follow-up questions present = {len(follow_up_questions)}")
        else:
            FAIL += 1
            ERRORS.append("Assistant turn expected at least three follow-up questions")
            print("  FAIL  Assistant turn expected at least three follow-up questions")
        assistant_trace_follow_ups = (
            body.get("data", {}).get("trace", {}).get("attributes", {}).get("follow_up_questions")
            if isinstance(body, dict)
            else None
        )
        if assistant_trace_follow_ups == follow_up_questions:
            PASS += 1
            print("  PASS  Assistant turn trace follow-up questions match response")
        else:
            FAIL += 1
            ERRORS.append("Assistant turn trace follow_up_questions expected to match response followUpQuestions")
            print("  FAIL  Assistant turn trace follow_up_questions expected to match response followUpQuestions")
        study_plan = body.get("data", {}).get("studyPlan") if isinstance(body, dict) else None
        study_steps = study_plan.get("steps") if isinstance(study_plan, dict) else None
        if isinstance(study_steps, list) and len(study_steps) >= 3:
            PASS += 1
            print(f"  PASS  Assistant turn study plan steps present = {len(study_steps)}")
        else:
            FAIL += 1
            ERRORS.append("Assistant turn expected at least three study plan steps")
            print("  FAIL  Assistant turn expected at least three study plan steps")
        assistant_trace_study_plan = (
            body.get("data", {}).get("trace", {}).get("attributes", {}).get("study_plan")
            if isinstance(body, dict)
            else None
        )
        if (
            isinstance(assistant_trace_study_plan, dict)
            and isinstance(study_plan, dict)
            and assistant_trace_study_plan.get("summary") == study_plan.get("summary")
            and assistant_trace_study_plan.get("steps") == study_plan.get("steps")
        ):
            PASS += 1
            print("  PASS  Assistant turn trace study plan matches response")
        else:
            FAIL += 1
            ERRORS.append("Assistant turn trace study_plan expected matching summary and steps")
            print("  FAIL  Assistant turn trace study_plan expected matching summary and steps")
        review_cards = body.get("data", {}).get("reviewCards") if isinstance(body, dict) else None
        if isinstance(review_cards, list) and len(review_cards) >= 2:
            PASS += 1
            print(f"  PASS  Assistant turn review cards present = {len(review_cards)}")
        else:
            FAIL += 1
            ERRORS.append("Assistant turn expected at least two review cards")
            print("  FAIL  Assistant turn expected at least two review cards")
        assistant_trace_review_cards = (
            body.get("data", {}).get("trace", {}).get("attributes", {}).get("review_cards")
            if isinstance(body, dict)
            else None
        )
        response_card_questions = [card.get("question") for card in review_cards if isinstance(card, dict)] if review_cards else []
        trace_card_questions = (
            [card.get("question") for card in assistant_trace_review_cards if isinstance(card, dict)]
            if assistant_trace_review_cards
            else []
        )
        if trace_card_questions == response_card_questions:
            PASS += 1
            print("  PASS  Assistant turn trace review cards match response questions")
        else:
            FAIL += 1
            ERRORS.append("Assistant turn trace review_cards expected matching response questions")
            print("  FAIL  Assistant turn trace review_cards expected matching response questions")
        weak_points = body.get("data", {}).get("weakPoints") if isinstance(body, dict) else None
        if isinstance(weak_points, list) and len(weak_points) >= 2:
            PASS += 1
            print(f"  PASS  Assistant turn weak points present = {len(weak_points)}")
        else:
            FAIL += 1
            ERRORS.append("Assistant turn expected at least two weak points")
            print("  FAIL  Assistant turn expected at least two weak points")

    # Correct URL: /api/chat/{sessionId}/messages (NOT /api/chat/sessions/{id}/messages)
    r, body = check("Add message", "POST", f"{BASE}/chat/{CREATED_SESSION_ID}/messages",
          json={"role": "user", "content": "Hello smoke test!",
                 "messageType": "TEXT"})
    if r is not None and r.status_code == 200:
        CREATED_MSG_ID = check_field("Message id", body, "data.id")
    check("List messages", "GET", f"{BASE}/chat/{CREATED_SESSION_ID}/messages")
    r, body = check("List weak points", "GET", f"{BASE}/chat/{CREATED_SESSION_ID}/weak-points")
    if r is not None and r.status_code == 200:
        weak_points = body.get("data") if isinstance(body, dict) else None
        if isinstance(weak_points, list) and len(weak_points) >= 2:
            PASS += 1
            print(f"  PASS  Persisted weak points present = {len(weak_points)}")
            r, body = check("Weak point summary", "GET",
                            f"{BASE}/chat/{CREATED_SESSION_ID}/weak-points/summary")
            if r is not None and r.status_code == 200:
                check_field("Weak point summary total", body, "data.totalCount")
                check_field("Weak point summary needs review", body, "data.needsReviewCount")
                check_field("Weak point summary due review", body, "data.dueReviewCount")
                check_field("Weak point summary next item", body, "data.nextWeakPoint.id")
            first_weak_point_id = weak_points[0].get("id") if isinstance(weak_points[0], dict) else None
            if first_weak_point_id:
                first_expected_answer = weak_points[0].get("expectedAnswer") if isinstance(weak_points[0], dict) else None
                r, body = check("Practice weak point turn", "POST",
                                f"{BASE}/chat/{CREATED_SESSION_ID}/weak-points/{first_weak_point_id}/practice-turn",
                                json={
                                    "strategyName": "advanced-rag",
                                    "topK": 4,
                                    "userAnswer": first_expected_answer or "GraphRAG traversal relationships and citations",
                                    "autoAssess": True,
                                })
                if r is not None and r.status_code == 200:
                    check_field("Practice weak point id", body, "data.weakPoint.id", first_weak_point_id)
                    check_field("Practice assistant message", body, "data.turn.assistantMessage.id")
                    check_field("Practice updated weak point id", body, "data.updatedWeakPoint.id", first_weak_point_id)
                    check_field("Practice assessment status", body, "data.assessment.masteryStatus", "MASTERED")
                    check_field("Practice summary completion", body, "data.summary.completionRate")
                    check_field("Practice updated practice count", body, "data.updatedWeakPoint.practiceCount")
                    check_field("Practice updated score", body, "data.updatedWeakPoint.lastPracticeScore")
                    next_review_at = check_field("Practice next review", body, "data.updatedWeakPoint.nextReviewAt")
                    check_datetime_after_now("Practice next review scheduled in future", next_review_at)
                    practice_cards = body.get("data", {}).get("turn", {}).get("reviewCards") if isinstance(body, dict) else None
                    if isinstance(practice_cards, list) and practice_cards:
                        PASS += 1
                        print(f"  PASS  Practice review cards present = {len(practice_cards)}")
                    else:
                        FAIL += 1
                        ERRORS.append("Weak point practice expected reviewCards")
                        print("  FAIL  Weak point practice expected reviewCards")
                    practice_weak_points = body.get("data", {}).get("turn", {}).get("weakPoints") if isinstance(body, dict) else None
                    if isinstance(practice_weak_points, list) and practice_weak_points:
                        PASS += 1
                        print(f"  PASS  Practice weak points present = {len(practice_weak_points)}")
                    else:
                        FAIL += 1
                        ERRORS.append("Weak point practice expected weakPoints")
                        print("  FAIL  Weak point practice expected weakPoints")
                r, body = check("Update weak point mastery", "PATCH",
                                f"{BASE}/chat/{CREATED_SESSION_ID}/weak-points/{first_weak_point_id}",
                                json={"masteryStatus": "MASTERED"})
                if r is not None and r.status_code == 200:
                    check_field("Weak point mastery status", body, "data.masteryStatus", "MASTERED")
                    r, body = check("List weak points after mastery update", "GET",
                                    f"{BASE}/chat/{CREATED_SESSION_ID}/weak-points")
                    reordered = body.get("data") if isinstance(body, dict) else None
                    if isinstance(reordered, list) and len(reordered) >= 2:
                        first_status = reordered[0].get("masteryStatus") if isinstance(reordered[0], dict) else None
                        if first_status == "NEEDS_REVIEW":
                            PASS += 1
                            print("  PASS  Weak point review order keeps NEEDS_REVIEW first")
                        else:
                            FAIL += 1
                            ERRORS.append("Weak point review order expected NEEDS_REVIEW first")
                            print("  FAIL  Weak point review order expected NEEDS_REVIEW first")
                    r, body = check("Weak point summary after mastery", "GET",
                                    f"{BASE}/chat/{CREATED_SESSION_ID}/weak-points/summary")
                    if r is not None and r.status_code == 200:
                        check_field("Weak point summary mastered count", body, "data.masteredCount")
                        check_field("Weak point summary completion rate", body, "data.completionRate")
        else:
            FAIL += 1
            ERRORS.append("Persisted weak points expected at least two rows")
            print("  FAIL  Persisted weak points expected at least two rows")


# ============================================================
section("6. FEEDBACK")
# ============================================================

# Feedback — needs real session+message IDs; runId optional if no run was created
fb_session_id = CREATED_SESSION_ID or TEST_UUID
fb_msg_id = CREATED_ASSISTANT_MSG_ID or CREATED_MSG_ID or TEST_UUID
fb_run_id = CREATED_RUN_ID or TEST_UUID
print(f"  INFO  Feedback: runId={fb_run_id} sessionId={fb_session_id} messageId={fb_msg_id}")
r, body = check("Create feedback", "POST", f"{BASE}/feedback",
                json={"runId": fb_run_id,
                       "sessionId": fb_session_id,
                       "messageId": fb_msg_id,
                       "rating": 4,
                       "feedbackType": "answer_quality",
                       "comment": "Smoke test feedback"},
                expect=[200, 404])  # 404 if run doesn't exist (no successful RAG query)


# ============================================================
section("7. CLEANUP")
# ============================================================

if CREATED_DOC_ID:
    check("Delete document", "DELETE", f"{BASE}/documents/{CREATED_DOC_ID}")

if CREATED_PARENT_DOC_ID:
    check("Delete parent-child document", "DELETE", f"{BASE}/documents/{CREATED_PARENT_DOC_ID}", expect=[200, 404])

if CREATED_EXP_ID:
    check("Delete experiment", "DELETE", f"{BASE}/rag/experiments/{CREATED_EXP_ID}")

if CREATED_KB_ID:
    check("Delete KB", "DELETE", f"{BASE}/knowledge-bases/{CREATED_KB_ID}")


# ============================================================
section("SUMMARY")
# ============================================================
TOTAL = PASS + FAIL
print(f"\n  Total: {TOTAL}  |  PASS: {PASS}  |  FAIL: {FAIL}")
if ERRORS:
    print(f"\n  Failures:")
    for e in ERRORS:
        print(f"    - {e}")
else:
    print("  All checks passed!")
print()

sys.exit(0 if FAIL == 0 else 1)

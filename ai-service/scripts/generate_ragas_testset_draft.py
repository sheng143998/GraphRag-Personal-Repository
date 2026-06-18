from __future__ import annotations

import argparse
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
AI_SERVICE_DIR = SCRIPT_DIR.parent
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from app.db.repositories import repository
from app.rag.evaluators.testset_generation import (
    DEFAULT_COMPLEX_QUESTION_TYPES,
    GENERATION_MODES,
    TestsetGenerationError,
    chunks_from_json,
    generate_case_drafts_by_mode,
    write_import_json,
    write_review_csv,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate DRAFT RAG evaluation cases from uploaded document chunks. "
            "The JSON output can be reviewed and imported through the existing Spring Boot evaluation-case API."
        ),
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--knowledge-base-id", help="Read chunks from the configured project repository/database.")
    source.add_argument("--chunks-json", help="Read chunks from a JSON array or {'items': [...]} file.")
    parser.add_argument("--output-json", required=True, help="Destination import JSON with DRAFT cases.")
    parser.add_argument("--review-csv", required=True, help="Destination UTF-8 BOM CSV for human review.")
    parser.add_argument(
        "--experiment-id",
        help=(
            "Optional Spring Boot RAG experiment UUID. When provided, output-json is wrapped as "
            "{'experimentId': ..., 'items': [...]} and can be posted to /api/rag/evaluation-cases/import."
        ),
    )
    parser.add_argument("--cases-per-document", type=int, default=3, help="Maximum draft cases per source document.")
    parser.add_argument("--top-k", type=int, default=5, help="Evaluation topK stored on each draft case.")
    parser.add_argument(
        "--generator-mode",
        "--generation-mode",
        dest="generator_mode",
        choices=sorted(GENERATION_MODES),
        default="rule",
        help="rule uses deterministic drafts; llm uses the configured LLM adapter; ragas/auto lazy-load optional RAGAS.",
    )
    parser.add_argument(
        "--question-types",
        default=",".join(DEFAULT_COMPLEX_QUESTION_TYPES),
        help="Comma-separated question type hints for LLM generation.",
    )
    parser.add_argument(
        "--ragas-testset-size",
        type=int,
        default=0,
        help="Total RAGAS TestsetGenerator size. Defaults to documents * cases-per-document.",
    )
    parser.add_argument(
        "--no-fallback",
        action="store_true",
        help="Fail instead of writing rule-based drafts when LLM/RAGAS generation is unavailable.",
    )
    args = parser.parse_args()

    if args.chunks_json:
        chunks = chunks_from_json(args.chunks_json)
    else:
        chunks = repository.list_chunks(args.knowledge_base_id)

    llm = None
    model_name = "llm"
    if args.generator_mode in {"llm", "auto"}:
        from app.services.adapters.registry import get_llm_model_name, llm_adapter

        llm = llm_adapter
        model_name = get_llm_model_name()

    try:
        result = generate_case_drafts_by_mode(
            chunks,
            mode=args.generator_mode,
            cases_per_document=args.cases_per_document,
            top_k=args.top_k,
            llm=llm,
            model_name=model_name,
            question_types=[item.strip() for item in args.question_types.split(",") if item.strip()],
            ragas_testset_size=args.ragas_testset_size or None,
            fallback_to_rules=not args.no_fallback,
        )
    except TestsetGenerationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    for warning in result.warnings:
        print(f"warning: {warning}", file=sys.stderr)

    drafts = result.drafts
    write_import_json(drafts, args.output_json, experiment_id=args.experiment_id)
    write_review_csv(drafts, args.review_csv)
    print(
        "generated "
        f"{len(drafts)} {result.mode} evaluation cases from {len(chunks)} chunks; "
        f"json={args.output_json}; reviewCsv={args.review_csv}; "
        f"experimentId={args.experiment_id or 'not-wrapped'}; "
        f"fallback={str(result.fallback_used).lower()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

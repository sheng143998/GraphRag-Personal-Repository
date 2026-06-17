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
    chunks_from_json,
    generate_case_drafts,
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
    parser.add_argument("--cases-per-document", type=int, default=3, help="Maximum draft cases per source document.")
    parser.add_argument("--top-k", type=int, default=5, help="Evaluation topK stored on each draft case.")
    args = parser.parse_args()

    if args.chunks_json:
        chunks = chunks_from_json(args.chunks_json)
    else:
        chunks = repository.list_chunks(args.knowledge_base_id)

    drafts = generate_case_drafts(
        chunks,
        cases_per_document=args.cases_per_document,
        top_k=args.top_k,
    )
    write_import_json(drafts, args.output_json)
    write_review_csv(drafts, args.review_csv)
    print(
        "generated "
        f"{len(drafts)} DRAFT evaluation cases from {len(chunks)} chunks; "
        f"json={args.output_json}; reviewCsv={args.review_csv}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

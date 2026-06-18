from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
AI_SERVICE_DIR = SCRIPT_DIR.parent
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from app.rag.evaluators.ragas_bridge import build_ragas_sample, write_jsonl
from app.schemas.rag import RagEvaluateRequest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert project RagEvaluateRequest JSON payloads to RAGAS JSONL rows.",
    )
    parser.add_argument("--input", required=True, help="JSON file containing one request, a list, or {'items': [...]}.")
    parser.add_argument("--output", required=True, help="Destination JSONL file.")
    args = parser.parse_args()

    payloads = _load_payloads(Path(args.input))
    rows = [_build_row_with_locator(raw) for raw in payloads]
    write_jsonl(rows, args.output)
    print(f"exported {len(rows)} RAGAS rows to {args.output}")
    return 0


def _load_payloads(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "items" in data:
        data = data["items"]
    elif isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError("input must be a JSON object, a JSON array, or an object with an items array")
    return [dict(item) for item in data if isinstance(item, dict)]


def _build_row_with_locator(raw: dict[str, object]) -> dict[str, object]:
    row = build_ragas_sample(RagEvaluateRequest.parse_obj(raw))
    metadata = dict(row.get("metadata") or {})
    for source_key, target_key in (
        ("evaluationId", "evaluation_id"),
        ("evaluation_id", "evaluation_id"),
        ("runId", "run_id"),
        ("run_id", "run_id"),
        ("experimentId", "experiment_id"),
        ("experiment_id", "experiment_id"),
        ("evaluationCaseId", "evaluation_case_id"),
        ("evaluation_case_id", "evaluation_case_id"),
    ):
        value = raw.get(source_key)
        if value:
            metadata[target_key] = str(value)
    if metadata:
        row["metadata"] = metadata
    return row


if __name__ == "__main__":
    raise SystemExit(main())

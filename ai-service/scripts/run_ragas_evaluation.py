from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
AI_SERVICE_DIR = SCRIPT_DIR.parent
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from app.rag.evaluators.ragas_bridge import DEFAULT_ID_METRICS, evaluate_with_ragas, read_jsonl


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run optional RAGAS metrics over JSONL rows exported from ai-service.",
    )
    parser.add_argument("--input", required=True, help="RAGAS JSONL dataset exported by export_ragas_dataset.py.")
    parser.add_argument("--output", required=True, help="Destination JSON report.")
    parser.add_argument(
        "--metrics",
        default=",".join(DEFAULT_ID_METRICS),
        help="Comma-separated RAGAS metric class names or aliases.",
    )
    args = parser.parse_args()

    metric_names = [item.strip() for item in args.metrics.split(",") if item.strip()]
    result = evaluate_with_ragas(read_jsonl(args.input), metric_names=metric_names)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(
        json.dumps(_serialize_result(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"wrote RAGAS report to {args.output}")
    return 0


def _serialize_result(result: object) -> object:
    if hasattr(result, "to_pandas"):
        dataframe = result.to_pandas()
        return json.loads(dataframe.to_json(orient="records", force_ascii=False))
    if hasattr(result, "scores"):
        return getattr(result, "scores")
    if hasattr(result, "dict"):
        return result.dict()
    return {"result": str(result)}


if __name__ == "__main__":
    raise SystemExit(main())

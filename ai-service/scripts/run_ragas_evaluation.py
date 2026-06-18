from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


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
    parser.add_argument(
        "--backfill-backend-url",
        help="Optional Spring Boot base URL, for example http://localhost:8080/api. When set, report rows are PUT back to the database.",
    )
    parser.add_argument("--ragas-version", default="", help="RAGAS runtime version to store with the report.")
    parser.add_argument("--judge-model", default="", help="Judge/generator model name to store with the report.")
    parser.add_argument("--report-uri", default="", help="Report URI/path to store with each backfilled evaluation.")
    args = parser.parse_args()

    metric_names = [item.strip() for item in args.metrics.split(",") if item.strip()]
    rows = read_jsonl(args.input)
    result = evaluate_with_ragas(rows, metric_names=metric_names)
    report = _serialize_result(result)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"wrote RAGAS report to {args.output}")
    if args.backfill_backend_url:
        count = _backfill_report(
            rows,
            report,
            backend_url=args.backfill_backend_url,
            metric_names=metric_names,
            ragas_version=args.ragas_version,
            judge_model=args.judge_model,
            report_uri=args.report_uri or str(Path(args.output).resolve()),
        )
        print(f"backfilled {count} RAGAS report rows to {args.backfill_backend_url}")
    return 0


def _serialize_result(result: object) -> Any:
    if hasattr(result, "to_pandas"):
        dataframe = result.to_pandas()
        return json.loads(dataframe.to_json(orient="records", force_ascii=False))
    if hasattr(result, "scores"):
        return getattr(result, "scores")
    if hasattr(result, "dict"):
        return result.dict()
    return {"result": str(result)}


def _backfill_report(
    input_rows: list[dict[str, object]],
    report: Any,
    *,
    backend_url: str,
    metric_names: list[str],
    ragas_version: str,
    judge_model: str,
    report_uri: str,
) -> int:
    report_rows = report if isinstance(report, list) else report.get("items", []) if isinstance(report, dict) else []
    if not isinstance(report_rows, list):
        raise ValueError("RAGAS report must be a row list for automatic backfill.")

    count = 0
    for index, report_row in enumerate(report_rows):
        if not isinstance(report_row, dict):
            continue
        input_row = input_rows[index] if index < len(input_rows) else {}
        payload = _build_backfill_payload(
            input_row=input_row,
            report_row=report_row,
            metric_names=metric_names,
            ragas_version=ragas_version,
            judge_model=judge_model,
            report_uri=report_uri,
        )
        if not _has_backfill_locator(payload):
            print(f"warning: skip report row {index + 1}; missing evaluationId or runId locator", file=sys.stderr)
            continue
        _put_json(_join_url(backend_url, "/rag/experiment-evaluations/ragas-report"), payload)
        count += 1
    return count


def _build_backfill_payload(
    *,
    input_row: dict[str, object],
    report_row: dict[str, object],
    metric_names: list[str],
    ragas_version: str,
    judge_model: str,
    report_uri: str,
) -> dict[str, object]:
    metadata = {}
    for candidate in (input_row.get("metadata"), report_row.get("metadata")):
      if isinstance(candidate, dict):
          metadata.update(candidate)

    return {
        "evaluationId": _first(metadata, "evaluation_id", "evaluationId"),
        "runId": _first(metadata, "run_id", "runId"),
        "experimentId": _first(metadata, "experiment_id", "experimentId"),
        "evaluationCaseId": _first(metadata, "evaluation_case_id", "evaluationCaseId"),
        "ragasScores": _extract_scores(report_row),
        "ragasMetricNames": metric_names,
        "ragasVersion": ragas_version or None,
        "ragasJudgeModel": judge_model or None,
        "ragasReportUri": report_uri or None,
    }


def _extract_scores(row: dict[str, object]) -> dict[str, object]:
    if isinstance(row.get("scores"), dict):
        return dict(row["scores"])
    ignored = {
        "user_input",
        "retrieved_contexts",
        "retrieved_context_ids",
        "response",
        "reference",
        "reference_context_ids",
        "metadata",
    }
    scores: dict[str, object] = {}
    for key, value in row.items():
        if key in ignored:
            continue
        if isinstance(value, (int, float, bool)) or value is None:
            scores[key] = value
    return scores


def _has_backfill_locator(payload: dict[str, object]) -> bool:
    return bool(payload.get("evaluationId") or (payload.get("runId") and (payload.get("experimentId") or payload.get("evaluationCaseId"))))


def _first(source: dict[str, object], *keys: str) -> str | None:
    for key in keys:
        value = source.get(key)
        if value:
            return str(value)
    return None


def _join_url(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + "/" + path.lstrip("/")


def _put_json(url: str, payload: dict[str, object]) -> None:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method="PUT",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status >= 300:
                raise RuntimeError(f"Backfill failed with HTTP {response.status}: {response.read().decode('utf-8')}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Backfill failed with HTTP {exc.code}: {body}") from exc


if __name__ == "__main__":
    raise SystemExit(main())

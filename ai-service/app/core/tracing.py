from __future__ import annotations

from contextvars import ContextVar, Token
from datetime import UTC, datetime
from time import perf_counter
from typing import Any
from uuid import uuid4

from app.schemas.common import TraceMetadata, TraceStep


_CURRENT_TRACE_ID: ContextVar[str | None] = ContextVar("current_trace_id", default=None)


def get_current_trace_id() -> str | None:
    return _CURRENT_TRACE_ID.get()


def set_current_trace_id(trace_id: str | None) -> Token:
    value = trace_id.strip() if trace_id else None
    return _CURRENT_TRACE_ID.set(value or None)


def reset_current_trace_id(token: Token) -> None:
    _CURRENT_TRACE_ID.reset(token)


class TraceBuilder:
    def __init__(
        self,
        *,
        operation: str,
        strategy_name: str,
        prompt_name: str | None = None,
        prompt_version: str | None = None,
        model_name: str | None = None,
        trace_id: str | None = None,
    ) -> None:
        self._started_at = perf_counter()
        resolved_trace_id = _resolve_trace_id(trace_id)
        self._trace = TraceMetadata(
            trace_id=resolved_trace_id,
            run_id=str(uuid4()),
            operation=operation,
            strategy_name=strategy_name,
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            model_name=model_name,
            started_at=datetime.now(UTC),
            steps=[],
            attributes={},
        )

    @property
    def trace(self) -> TraceMetadata:
        return self._trace

    def set_attribute(self, key: str, value: object) -> None:
        self._trace.attributes[key] = value

    def add_step(
        self,
        *,
        name: str,
        status: str,
        detail: str,
        model_name: str | None = None,
        payload: dict[str, object] | None = None,
    ) -> None:
        self._trace.steps.append(
            TraceStep(
                name=name,
                status=status,
                detail=detail,
                model_name=model_name,
                payload=payload or {},
                timestamp=datetime.now(UTC),
            )
        )

    def record_adapter_metadata(self, metadata: dict[str, Any]) -> dict[str, object]:
        calls = metadata.get("adapter_calls")
        if not isinstance(calls, list):
            return {}

        token_usage = dict(self._trace.attributes.get("token_usage") or {})
        latency_breakdown = dict(self._trace.attributes.get("latency_breakdown") or {})
        recorded_calls: list[dict[str, object]] = list(self._trace.attributes.get("adapter_calls") or [])
        latest_summary: dict[str, object] = {}

        for call in calls:
            if not isinstance(call, dict):
                continue
            operation = str(call.get("operation") or "model_call")
            latency_ms = _number(call.get("latency_ms"))
            usage = call.get("usage") if isinstance(call.get("usage"), dict) else {}
            if latency_ms is not None:
                latency_breakdown[operation] = round(latency_breakdown.get(operation, 0) + latency_ms, 3)
                latest_summary["latency_ms"] = latency_ms
            if usage:
                _merge_usage(token_usage, operation=operation, usage=usage)
                latest_summary["usage"] = usage
            recorded_call = {
                key: value
                for key, value in call.items()
                if key not in {"usage"} or value
            }
            recorded_calls.append(recorded_call)
            latest_summary.update(
                {
                    "operation": operation,
                    "model_name": call.get("model_name"),
                    "endpoint": call.get("endpoint"),
                }
            )

        if token_usage:
            self._trace.attributes["token_usage"] = token_usage
        if latency_breakdown:
            self._trace.attributes["latency_breakdown"] = latency_breakdown
        if recorded_calls:
            self._trace.attributes["adapter_calls"] = recorded_calls
        calls.clear()
        return latest_summary

    def finalize(self, *, status: str, error_message: str | None = None) -> TraceMetadata:
        self._trace.status = status
        self._trace.error_message = error_message
        self._trace.finished_at = datetime.now(UTC)
        self._trace.latency_ms = round((perf_counter() - self._started_at) * 1000, 3)
        return self._trace


def _resolve_trace_id(trace_id: str | None) -> str:
    if trace_id and trace_id.strip():
        return trace_id.strip()
    current_trace_id = get_current_trace_id()
    if current_trace_id:
        return current_trace_id
    return str(uuid4())


def _merge_usage(target: dict[str, object], *, operation: str, usage: dict[str, object]) -> None:
    for source_key, target_key in {
        "prompt_tokens": "prompt_tokens",
        "input_tokens": "prompt_tokens",
        "completion_tokens": "completion_tokens",
        "output_tokens": "completion_tokens",
        "total_tokens": "total_tokens",
    }.items():
        value = _number(usage.get(source_key))
        if value is not None:
            target[target_key] = int(target.get(target_key, 0) or 0) + int(value)

    if operation.startswith("embed"):
        token_value = _number(usage.get("total_tokens") or usage.get("input_tokens") or usage.get("prompt_tokens"))
        if token_value is not None:
            target["embedding_tokens"] = int(target.get("embedding_tokens", 0) or 0) + int(token_value)
    if operation == "rerank":
        token_value = _number(usage.get("total_tokens") or usage.get("input_tokens") or usage.get("prompt_tokens"))
        if token_value is not None:
            target["rerank_tokens"] = int(target.get("rerank_tokens", 0) or 0) + int(token_value)

    cost = _number(usage.get("estimated_cost") or usage.get("cost"))
    if cost is not None:
        target["estimated_cost"] = round(float(target.get("estimated_cost", 0) or 0) + cost, 8)


def _number(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None

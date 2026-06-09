from __future__ import annotations

from contextvars import ContextVar, Token
from datetime import UTC, datetime
from time import perf_counter
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

from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from app.schemas.common import TraceMetadata, TraceStep


class TraceBuilder:
    def __init__(
        self,
        *,
        operation: str,
        strategy_name: str,
        prompt_name: str | None = None,
        prompt_version: str | None = None,
        model_name: str | None = None,
    ) -> None:
        self._started_at = perf_counter()
        self._trace = TraceMetadata(
            trace_id=str(uuid4()),
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

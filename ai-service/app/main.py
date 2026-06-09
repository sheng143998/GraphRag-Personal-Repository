import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request

from app.api.router import api_router
from app.core.config import settings
from app.core.tracing import reset_current_trace_id, set_current_trace_id

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
log = logging.getLogger("ai_service.request")
TRACE_HEADER_NAME = "X-Trace-Id"

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    trace_id = request.headers.get(TRACE_HEADER_NAME, "").strip() or str(uuid4())
    trace_token = set_current_trace_id(trace_id)
    started = time.perf_counter()
    log.info(
        "AI request start: method=%s, path=%s, traceId=%s",
        request.method,
        request.url.path,
        trace_id,
    )
    try:
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = int((time.perf_counter() - started) * 1000)
            log.exception(
                "AI request failed: method=%s, path=%s, durationMs=%s, traceId=%s",
                request.method,
                request.url.path,
                duration_ms,
                trace_id,
            )
            raise
        duration_ms = int((time.perf_counter() - started) * 1000)
        response.headers[TRACE_HEADER_NAME] = trace_id
        log.info(
            "AI request completed: method=%s, path=%s, status=%s, durationMs=%s, traceId=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            trace_id,
        )
        return response
    finally:
        reset_current_trace_id(trace_token)


app.include_router(api_router, prefix="/ai")

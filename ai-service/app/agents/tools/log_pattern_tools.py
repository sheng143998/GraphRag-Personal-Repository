from __future__ import annotations

import re


ERROR_CODE_PATTERN = re.compile(r"\b(?:HTTP\s*)?(?:[45]\d{2}|P[0-3]|SEV[0-4]|ERR[-_A-Z0-9]+)\b", re.IGNORECASE)
TRACE_ID_PATTERN = re.compile(r"\b(?:trace[_-]?id|request[_-]?id|x-trace-id)[:=\s]+([A-Za-z0-9._:-]{6,})", re.IGNORECASE)


def extract_error_codes(text: str) -> list[str]:
    return _dedupe(match.group(0).strip() for match in ERROR_CODE_PATTERN.finditer(text))


def extract_trace_ids(text: str) -> list[str]:
    return _dedupe(match.group(1).strip() for match in TRACE_ID_PATTERN.finditer(text))


def has_log_or_code_signal(text: str) -> bool:
    lowered = text.lower()
    markers = (
        "traceback",
        "exception",
        "stack trace",
        "nullpointer",
        "timeout",
        "connection refused",
        "error:",
        "warn",
        "日志",
        "堆栈",
        "报错",
        "异常",
        "日志",
        "堆栈",
        "报错",
        "异常",
        "trace id",
        "trace_id",
    )
    return any(marker in lowered for marker in markers) or bool(extract_error_codes(text) or extract_trace_ids(text))


def classify_log_error(text: str) -> tuple[str, str, list[str], list[str]]:
    lowered = text.lower()
    key_signals: list[str] = []
    unsafe_actions: list[str] = []
    error_type = "unknown"
    component = "unknown"

    if any(term in lowered for term in ("504", "gateway timeout", "timeout", "timed out")):
        error_type = "timeout"
        component = "gateway-or-upstream-service"
        key_signals.append("Detected timeout / 504 style signal.")
    if any(term in lowered for term in ("401", "403", "unauthorized", "forbidden", "鉴权", "权限")):
        error_type = "authentication-or-authorization"
        component = "auth-service"
        key_signals.append("Detected authentication or authorization signal.")
    if any(term in lowered for term in ("connection refused", "connection reset", "connectexception")):
        error_type = "network-connection"
        component = "network-or-service-endpoint"
        key_signals.append("Detected network connection failure signal.")
    if any(term in lowered for term in ("sql", "database", "deadlock", "connection pool", "数据库")):
        error_type = "database"
        component = "database"
        key_signals.append("Detected database related signal.")
    if any(term in lowered for term in ("nullpointer", "keyerror", "indexerror", "traceback", "stack trace")):
        error_type = "application-exception"
        component = "application-service"
        key_signals.append("Detected application exception or stack trace signal.")
    if any(term in lowered for term in ("delete", "drop table", "truncate", "回滚", "重启", "restart")):
        unsafe_actions.append("Potential destructive or production-changing operation mentioned.")

    if any(term in lowered for term in ("鉴权", "权限")):
        error_type = "authentication-or-authorization"
        component = "auth-service"
        key_signals.append("Detected authentication or authorization signal.")
    if any(term in lowered for term in ("数据库", "死锁", "连接池")):
        error_type = "database"
        component = "database"
        key_signals.append("Detected database related signal.")
    if any(term in lowered for term in ("堆栈", "空指针", "异常")):
        error_type = "application-exception"
        component = "application-service"
        key_signals.append("Detected application exception or stack trace signal.")
    if any(term in lowered for term in ("删除", "清空", "回滚", "重启", "发布", "配置")):
        unsafe_actions.append("Potential destructive or production-changing operation mentioned.")

    if not key_signals:
        key_signals.append("No known log pattern matched; keep this as a manual review signal.")

    safe_checks = [
        "Confirm affected time window and trace id before changing production.",
        "Compare customer-visible error with service logs and gateway logs.",
        "Check recent release, configuration, traffic, or dependency changes.",
    ]
    return error_type, component, key_signals, unsafe_actions or []


def _dedupe(values) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = str(value).strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(normalized)
    return result

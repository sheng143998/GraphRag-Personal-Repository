from __future__ import annotations

import re

from app.agents.states.support_state import ClarificationResult, IncidentContext, SupportAgentState
from app.agents.tools.log_pattern_tools import extract_error_codes, extract_trace_ids, has_log_or_code_signal


class ClarificationAgent:
    name = "clarification_agent"

    def run(self, state: SupportAgentState) -> ClarificationResult:
        text = state.request.user_input.strip()
        lowered = text.lower()
        error_codes = extract_error_codes(text)
        trace_ids = extract_trace_ids(text)
        incident = IncidentContext(
            product_name=_first_variable(state, "product", "product_name", "productName"),
            module_name=_detect_module(text),
            version=_detect_version(text),
            environment=_detect_environment(text),
            tenant_or_region=_first_variable(state, "tenant", "region", "tenant_or_region"),
            symptom=_short_symptom(text),
            error_codes=error_codes,
            log_snippets=[text] if has_log_or_code_signal(text) else [],
            trace_ids=trace_ids,
            impact_scope=_detect_impact(text),
            severity_hint=_detect_severity(text),
            recent_changes=_detect_recent_changes(text),
            attempted_actions=[],
            customer_expectation="restore service" if _contains_any(lowered, ("down", "unavailable", "无法", "不可用")) else "",
        )

        missing = []
        if not incident.symptom:
            missing.append("fault_symptom")
        if not (incident.product_name or incident.module_name):
            missing.append("product_or_module")
        if not incident.impact_scope:
            missing.append("impact_scope")
        if not (incident.error_codes or incident.trace_ids or incident.log_snippets):
            missing.append("error_code_log_or_trace_id")

        incident.missing_fields = missing
        state.incident = incident
        state.route.has_log_or_code_signal = bool(incident.log_snippets or incident.error_codes or incident.trace_ids)

        questions = _questions_for_missing(missing)
        can_continue = not _requires_user_clarification(missing, incident)
        result = ClarificationResult(
            can_continue=can_continue,
            missing_required_fields=missing,
            clarification_questions=questions,
            confidence=0.85 if not missing else 0.55,
        )
        state.clarification = result
        if not can_continue:
            state.route.early_return = True
            state.route.final_status = "needs_clarification"
        return result


def _first_variable(state: SupportAgentState, *keys: str) -> str:
    variables = state.request.variables or {}
    for key in keys:
        value = variables.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _short_symptom(text: str) -> str:
    words = text.split()
    if not words:
        return ""
    return " ".join(words[:24])[:180]


def _detect_module(text: str) -> str:
    lowered = text.lower()
    for module in ("登录", "鉴权", "网关", "接口", "数据库", "队列", "控制台"):
        if module in text:
            return module
    for module in ("login", "auth", "gateway", "api", "database", "queue", "payment", "console"):
        if module in lowered:
            return module
    for module in ("登录", "鉴权", "网关", "接口", "数据库", "队列", "控制台"):
        if module in text:
            return module
    return ""


def _detect_version(text: str) -> str:
    match = re.search(r"\b(?:v|version|版本)\s*[:=]?\s*([0-9]+(?:\.[0-9]+){1,3})\b", text, re.IGNORECASE)
    return match.group(1) if match else ""


def _detect_environment(text: str) -> str:
    utf8_match = _detect_environment_utf8(text)
    if utf8_match:
        return utf8_match
    lowered = text.lower()
    if _contains_any(lowered, ("prod", "production", "生产")):
        return "production"
    if _contains_any(lowered, ("staging", "预发")):
        return "staging"
    if _contains_any(lowered, ("test", "测试")):
        return "test"
    return ""


def _detect_impact(text: str) -> str:
    utf8_match = _detect_impact_utf8(text)
    if utf8_match:
        return utf8_match
    lowered = text.lower()
    if _contains_any(lowered, ("all users", "global", "entire site", "全站", "大面积", "全部用户")):
        return "major"
    if _contains_any(lowered, ("some users", "partial", "部分", "个别", "偶发")):
        return "partial"
    if _contains_any(lowered, ("customer", "tenant", "客户", "租户")):
        return "customer"
    return ""


def _detect_severity(text: str) -> str:
    utf8_match = _detect_severity_utf8(text)
    if utf8_match:
        return utf8_match
    lowered = text.lower()
    if _contains_any(lowered, ("p0", "critical", "sev0", "sev1", "outage", "down", "全站", "大面积", "不可用")):
        return "critical"
    if _contains_any(lowered, ("p1", "high", "sev2", "严重", "紧急", "影响生产", "无法登录")):
        return "high"
    if _contains_any(lowered, ("p2", "medium", "部分", "偶发")):
        return "medium"
    return "low"


def _detect_recent_changes(text: str) -> list[str]:
    lowered = text.lower()
    changes = _detect_recent_changes_utf8(text)
    if _contains_any(lowered, ("release", "deploy", "发布", "上线")):
        changes.append("recent_release")
    if _contains_any(lowered, ("config", "configuration", "配置")):
        changes.append("configuration_change")
    if _contains_any(lowered, ("import", "migration", "导入", "迁移")):
        changes.append("data_change")
    if _contains_any(lowered, ("traffic", "流量", "峰值")):
        changes.append("traffic_change")
    return changes


def _requires_user_clarification(missing: list[str], incident: IncidentContext) -> bool:
    if len(missing) >= 3:
        return True
    if "fault_symptom" in missing:
        return True
    if "error_code_log_or_trace_id" in missing and incident.severity_hint not in {"critical", "high"}:
        return True
    return False


def _questions_for_missing(missing: list[str]) -> list[str]:
    mapping = {
        "fault_symptom": "请补充客户看到的具体现象、报错页面或失败操作。",
        "product_or_module": "请补充受影响的产品、模块、接口或服务名称。",
        "impact_scope": "请补充影响范围：全站、单客户、部分用户、区域或租户。",
        "error_code_log_or_trace_id": "请补充错误码、关键日志片段或 trace id，三者至少一个。",
    }
    return [mapping[key] for key in missing if key in mapping]


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _detect_environment_utf8(text: str) -> str:
    lowered = text.lower()
    if _contains_any(lowered, ("生产",)):
        return "production"
    if _contains_any(lowered, ("预发",)):
        return "staging"
    if _contains_any(lowered, ("测试",)):
        return "test"
    return ""


def _detect_impact_utf8(text: str) -> str:
    lowered = text.lower()
    if _contains_any(lowered, ("全站", "大面积", "全部用户")):
        return "major"
    if _contains_any(lowered, ("部分", "个别", "偶发")):
        return "partial"
    if _contains_any(lowered, ("客户", "租户")):
        return "customer"
    return ""


def _detect_severity_utf8(text: str) -> str:
    lowered = text.lower()
    if _contains_any(lowered, ("p0", "全站", "大面积", "不可用")):
        return "critical"
    if _contains_any(lowered, ("p1", "严重", "紧急", "影响生产", "无法登录")):
        return "high"
    if _contains_any(lowered, ("p2", "部分", "偶发")):
        return "medium"
    return ""


def _detect_recent_changes_utf8(text: str) -> list[str]:
    lowered = text.lower()
    changes = []
    if _contains_any(lowered, ("发布", "上线")):
        changes.append("recent_release")
    if _contains_any(lowered, ("配置",)):
        changes.append("configuration_change")
    if _contains_any(lowered, ("导入", "迁移")):
        changes.append("data_change")
    if _contains_any(lowered, ("流量", "峰值")):
        changes.append("traffic_change")
    return changes

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.agents.tools.log_pattern_tools import classify_log_error, extract_error_codes, extract_trace_ids


class SupportLogPatternInput(BaseModel):
    text: str = Field(..., description="Customer provided logs, error text, code snippet, or incident note.")


def analyze_support_log_patterns(text: str) -> dict[str, Any]:
    error_type, component, key_signals, unsafe_actions = classify_log_error(text)
    return {
        "detected_error_type": error_type,
        "suspected_component": component,
        "key_signals": key_signals,
        "unsafe_actions": unsafe_actions,
        "error_codes": extract_error_codes(text),
        "trace_ids": extract_trace_ids(text),
        "confidence": 0.75 if error_type != "unknown" else 0.45,
    }


def build_support_log_pattern_tool() -> Any:
    """Build the LangChain StructuredTool for support log/code signal extraction."""
    from langchain_core.tools import StructuredTool

    return StructuredTool.from_function(
        func=analyze_support_log_patterns,
        name="analyze_support_log_patterns",
        description=(
            "Extract error codes, trace ids, likely component, safe evidence signals, "
            "and risky production actions from a support incident note."
        ),
        args_schema=SupportLogPatternInput,
    )

from __future__ import annotations

from app.agents.states.support_state import CodeLogAnalysisResult, SupportAgentState
from app.agents.tools.log_pattern_tools import classify_log_error


class CodeLogToolAgent:
    name = "code_log_tool_agent"

    def run(self, state: SupportAgentState) -> CodeLogAnalysisResult:
        text = "\n".join(state.incident.log_snippets) or state.request.user_input
        error_type, component, key_signals, unsafe_actions = classify_log_error(text)
        result = CodeLogAnalysisResult(
            triggered=True,
            detected_error_type=error_type,
            suspected_component=component,
            key_signals=key_signals,
            timeline_hints=["Align log timestamp with customer report time and recent change window."],
            safe_checks=[
                "Collect gateway, application, and dependency logs for the same trace id.",
                "Check health, saturation, error rate, and recent deployment/configuration changes.",
            ],
            unsafe_actions=unsafe_actions,
            confidence=0.75 if error_type != "unknown" else 0.45,
        )
        state.log_analysis = result
        return result


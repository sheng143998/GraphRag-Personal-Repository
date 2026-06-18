from __future__ import annotations

from app.agents.states.support_state import CodeLogAnalysisResult, SupportAgentState
from app.agents.tools.support_langchain_tools import analyze_support_log_patterns


class CodeLogToolAgent:
    name = "code_log_tool_agent"

    def run(self, state: SupportAgentState) -> CodeLogAnalysisResult:
        text = "\n".join(state.incident.log_snippets) or state.request.user_input
        analysis = analyze_support_log_patterns(text)
        result = CodeLogAnalysisResult(
            triggered=True,
            detected_error_type=str(analysis["detected_error_type"]),
            suspected_component=str(analysis["suspected_component"]),
            key_signals=list(analysis["key_signals"]),
            timeline_hints=["Align log timestamp with customer report time and recent change window."],
            safe_checks=[
                "Collect gateway, application, and dependency logs for the same trace id.",
                "Check health, saturation, error rate, and recent deployment/configuration changes.",
            ],
            unsafe_actions=list(analysis["unsafe_actions"]),
            confidence=float(analysis["confidence"]),
        )
        state.log_analysis = result
        return result

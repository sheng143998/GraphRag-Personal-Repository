package com.example.agentknowledge.client.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
import java.util.Map;

public record AiAgentInvokeResponse(
        @JsonProperty("agent_name") String agentName,
        String output,
        List<AiSourceMetadata> citations,
        @JsonProperty("question_type") String questionType,
        @JsonProperty("selected_strategy_name") String selectedStrategyName,
        @JsonProperty("workflow_steps") List<WorkflowStep> workflowSteps,
        AiTraceMetadata trace
) {
    public record WorkflowStep(
            String name,
            String detail,
            Map<String, Object> payload
    ) {
    }
}

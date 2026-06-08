package com.example.agentknowledge.dto.agent;

import com.example.agentknowledge.client.dto.AiSourceMetadata;
import com.example.agentknowledge.client.dto.AiTraceMetadata;
import java.util.List;
import java.util.Map;

public record AgentInvokeResponse(
        String agentName,
        String output,
        List<AiSourceMetadata> citations,
        String questionType,
        String selectedStrategyName,
        List<String> followUpQuestions,
        StudyPlan studyPlan,
        List<WorkflowStep> workflowSteps,
        AiTraceMetadata trace
) {
    public record StudyPlan(
            String summary,
            List<String> focusAreas,
            List<String> steps
    ) {
    }

    public record WorkflowStep(
            String name,
            String detail,
            Map<String, Object> payload
    ) {
    }
}

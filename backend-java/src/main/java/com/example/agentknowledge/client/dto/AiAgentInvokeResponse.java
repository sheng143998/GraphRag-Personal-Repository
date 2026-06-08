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
        @JsonProperty("follow_up_questions") List<String> followUpQuestions,
        @JsonProperty("study_plan") StudyPlan studyPlan,
        @JsonProperty("review_cards") List<ReviewCard> reviewCards,
        @JsonProperty("workflow_steps") List<WorkflowStep> workflowSteps,
        AiTraceMetadata trace
) {
    public record StudyPlan(
            String summary,
            @JsonProperty("focus_areas") List<String> focusAreas,
            List<String> steps
    ) {
    }

    public record ReviewCard(
            String question,
            @JsonProperty("expected_answer") String expectedAnswer,
            @JsonProperty("source_hint") String sourceHint,
            String difficulty
    ) {
    }

    public record WorkflowStep(
            String name,
            String detail,
            Map<String, Object> payload
    ) {
    }
}

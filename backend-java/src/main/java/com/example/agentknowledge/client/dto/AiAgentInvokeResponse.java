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
        @JsonProperty("support_plan") SupportPlan supportPlan,
        @JsonProperty("workflow_steps") List<WorkflowStep> workflowSteps,
        AiTraceMetadata trace,
        @JsonProperty("rag_trace") AiTraceMetadata ragTrace
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

    public record SupportPlan(
            @JsonProperty("issue_summary") String issueSummary,
            @JsonProperty("clarification_questions") List<String> clarificationQuestions,
            @JsonProperty("evidence_references") List<String> evidenceReferences,
            @JsonProperty("diagnostic_steps") List<DiagnosticStep> diagnosticSteps,
            EscalationRecommendation escalation,
            @JsonProperty("risk_notes") List<String> riskNotes,
            @JsonProperty("next_actions") List<String> nextActions
    ) {
    }

    public record DiagnosticStep(
            Integer order,
            String action,
            @JsonProperty("expected_signal") String expectedSignal,
            @JsonProperty("evidence_hint") String evidenceHint,
            String fallback
    ) {
    }

    public record EscalationRecommendation(
            Boolean required,
            String severity,
            String reason,
            @JsonProperty("suggested_queue") String suggestedQueue,
            @JsonProperty("ticket_summary") String ticketSummary,
            @JsonProperty("ticket_fields") Map<String, Object> ticketFields
    ) {
    }

    public record WorkflowStep(
            String name,
            String detail,
            Map<String, Object> payload
    ) {
    }
}

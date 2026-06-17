package com.example.agentknowledge.service;

import com.example.agentknowledge.client.AiServiceGateway;
import com.example.agentknowledge.client.dto.AiAgentInvokeRequest;
import com.example.agentknowledge.client.dto.AiAgentInvokeResponse;
import com.example.agentknowledge.common.api.TraceContext;
import com.example.agentknowledge.dto.agent.AgentInvokeRequest;
import com.example.agentknowledge.dto.agent.AgentInvokeResponse;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;

@Service
public class AgentService {

    private final AiServiceGateway aiServiceGateway;

    public AgentService(AiServiceGateway aiServiceGateway) {
        this.aiServiceGateway = aiServiceGateway;
    }

    public AgentInvokeResponse invoke(AgentInvokeRequest request) {
        AiAgentInvokeResponse aiResponse = aiServiceGateway.invokeAgent(
                new AiAgentInvokeRequest(
                        defaultString(request.agentName(), "study-agent"),
                        request.userInput(),
                        defaultString(request.strategyName(), "basic-rag"),
                        request.topK() != null ? request.topK() : 5,
                        new AiAgentInvokeRequest.Context(
                                request.knowledgeBaseId(),
                                request.sessionId(),
                                request.messageId(),
                                request.metadataFilters() != null ? request.metadataFilters() : Map.of(),
                                request.retrievalOptions() != null ? request.retrievalOptions() : Map.of()
                        ),
                        request.variables() != null ? request.variables() : Map.of()
                ),
                TraceContext.getTraceId()
        );

        return new AgentInvokeResponse(
                aiResponse.agentName(),
                aiResponse.output(),
                aiResponse.citations(),
                aiResponse.questionType(),
                aiResponse.selectedStrategyName(),
                aiResponse.followUpQuestions() != null ? aiResponse.followUpQuestions() : List.of(),
                mapStudyPlan(aiResponse.studyPlan()),
                mapReviewCards(aiResponse.reviewCards()),
                mapSupportPlan(aiResponse.supportPlan()),
                mapWorkflowSteps(aiResponse.workflowSteps()),
                aiResponse.trace(),
                aiResponse.ragTrace()
        );
    }

    private static AgentInvokeResponse.StudyPlan mapStudyPlan(AiAgentInvokeResponse.StudyPlan studyPlan) {
        if (studyPlan == null) {
            return null;
        }
        return new AgentInvokeResponse.StudyPlan(
                studyPlan.summary(),
                studyPlan.focusAreas() != null ? studyPlan.focusAreas() : List.of(),
                studyPlan.steps() != null ? studyPlan.steps() : List.of()
        );
    }

    private static List<AgentInvokeResponse.ReviewCard> mapReviewCards(
            List<AiAgentInvokeResponse.ReviewCard> reviewCards
    ) {
        if (reviewCards == null) {
            return List.of();
        }
        return reviewCards.stream()
                .map(card -> new AgentInvokeResponse.ReviewCard(
                        card.question(),
                        card.expectedAnswer(),
                        card.sourceHint() != null ? card.sourceHint() : "",
                        card.difficulty() != null ? card.difficulty() : "medium"
                ))
                .toList();
    }

    private static AgentInvokeResponse.SupportPlan mapSupportPlan(AiAgentInvokeResponse.SupportPlan supportPlan) {
        if (supportPlan == null) {
            return null;
        }
        return new AgentInvokeResponse.SupportPlan(
                supportPlan.issueSummary(),
                supportPlan.clarificationQuestions() != null ? supportPlan.clarificationQuestions() : List.of(),
                supportPlan.evidenceReferences() != null ? supportPlan.evidenceReferences() : List.of(),
                mapDiagnosticSteps(supportPlan.diagnosticSteps()),
                mapEscalation(supportPlan.escalation()),
                supportPlan.riskNotes() != null ? supportPlan.riskNotes() : List.of(),
                supportPlan.nextActions() != null ? supportPlan.nextActions() : List.of()
        );
    }

    private static List<AgentInvokeResponse.DiagnosticStep> mapDiagnosticSteps(
            List<AiAgentInvokeResponse.DiagnosticStep> diagnosticSteps
    ) {
        if (diagnosticSteps == null) {
            return List.of();
        }
        return diagnosticSteps.stream()
                .map(step -> new AgentInvokeResponse.DiagnosticStep(
                        step.order(),
                        step.action(),
                        step.expectedSignal() != null ? step.expectedSignal() : "",
                        step.evidenceHint() != null ? step.evidenceHint() : "",
                        step.fallback() != null ? step.fallback() : ""
                ))
                .toList();
    }

    private static AgentInvokeResponse.EscalationRecommendation mapEscalation(
            AiAgentInvokeResponse.EscalationRecommendation escalation
    ) {
        if (escalation == null) {
            return new AgentInvokeResponse.EscalationRecommendation(
                    false,
                    "low",
                    "",
                    "technical-support",
                    "",
                    Map.of()
            );
        }
        return new AgentInvokeResponse.EscalationRecommendation(
                escalation.required() != null ? escalation.required() : false,
                escalation.severity() != null ? escalation.severity() : "low",
                escalation.reason() != null ? escalation.reason() : "",
                escalation.suggestedQueue() != null ? escalation.suggestedQueue() : "technical-support",
                escalation.ticketSummary() != null ? escalation.ticketSummary() : "",
                escalation.ticketFields() != null ? escalation.ticketFields() : Map.of()
        );
    }

    private static List<AgentInvokeResponse.WorkflowStep> mapWorkflowSteps(
            List<AiAgentInvokeResponse.WorkflowStep> workflowSteps
    ) {
        if (workflowSteps == null) {
            return List.of();
        }
        return workflowSteps.stream()
                .map(step -> new AgentInvokeResponse.WorkflowStep(
                        step.name(),
                        step.detail(),
                        step.payload() != null ? step.payload() : Map.of()
                ))
                .toList();
    }

    private static String defaultString(String value, String fallback) {
        return value != null && !value.isBlank() ? value : fallback;
    }
}

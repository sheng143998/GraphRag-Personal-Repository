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
                                request.metadataFilters() != null ? request.metadataFilters() : Map.of()
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
                mapWorkflowSteps(aiResponse.workflowSteps()),
                aiResponse.trace()
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

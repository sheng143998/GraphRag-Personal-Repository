package com.example.agentknowledge.dto.chat;

import com.example.agentknowledge.dto.agent.AgentInvokeResponse;

public record AssistantTurnResponse(
        ChatMessageResponse userMessage,
        ChatMessageResponse assistantMessage,
        String agentName,
        String questionType,
        String selectedStrategyName,
        java.util.List<String> followUpQuestions,
        java.util.List<AgentInvokeResponse.WorkflowStep> workflowSteps,
        Object trace
) {
}

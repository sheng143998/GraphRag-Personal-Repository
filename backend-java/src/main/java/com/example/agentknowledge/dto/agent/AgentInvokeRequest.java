package com.example.agentknowledge.dto.agent;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.util.Map;
import java.util.UUID;

public record AgentInvokeRequest(
        String agentName,
        @NotBlank String userInput,
        String strategyName,
        @Min(1) @Max(20) Integer topK,
        @NotNull UUID knowledgeBaseId,
        UUID sessionId,
        UUID messageId,
        Map<String, Object> metadataFilters,
        Map<String, Object> retrievalOptions,
        Map<String, Object> variables
) {
}

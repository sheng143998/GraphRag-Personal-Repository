package com.example.agentknowledge.dto.chat;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import java.util.Map;

public record CreateAssistantTurnRequest(
        @NotBlank String userInput,
        String agentName,
        String strategyName,
        @Min(1) @Max(20) Integer topK,
        Map<String, Object> metadataFilters,
        Map<String, Object> variables
) {
}

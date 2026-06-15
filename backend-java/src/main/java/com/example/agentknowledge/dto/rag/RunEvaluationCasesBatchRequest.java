package com.example.agentknowledge.dto.rag;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.List;
import java.util.Map;
import java.util.UUID;

public record RunEvaluationCasesBatchRequest(
        @NotNull UUID experimentId,
        List<UUID> caseIds,
        @Size(max = 100) String strategyName,
        @Size(max = 100) String retrieverType,
        Integer topK,
        Map<String, Object> metadataFilters,
        Map<String, Object> retrievalOptions
) {
}

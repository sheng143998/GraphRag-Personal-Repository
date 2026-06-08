package com.example.agentknowledge.dto.rag;

import java.time.Instant;
import java.util.UUID;

public record RagExperimentEvaluationHistoryResponse(
        UUID id,
        UUID experimentId,
        String experimentName,
        UUID runId,
        String runQuestion,
        String runStrategyName,
        String runRetrieverType,
        String runModelName,
        Long runLatencyMs,
        Instant runCreatedAt,
        Double groundedScore,
        Double retrievalScore,
        String expectedAnswer,
        String generatedAnswer,
        String notes,
        Instant createdAt
) {
}

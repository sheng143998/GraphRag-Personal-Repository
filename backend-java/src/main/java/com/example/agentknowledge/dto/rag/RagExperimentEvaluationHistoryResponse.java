package com.example.agentknowledge.dto.rag;

import java.time.Instant;
import java.util.UUID;

public record RagExperimentEvaluationHistoryResponse(
        UUID id,
        UUID experimentId,
        UUID runId,
        Double groundedScore,
        Double retrievalScore,
        String expectedAnswer,
        String generatedAnswer,
        String notes,
        Instant createdAt
) {
}

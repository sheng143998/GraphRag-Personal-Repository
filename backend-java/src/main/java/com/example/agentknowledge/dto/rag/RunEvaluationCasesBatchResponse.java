package com.example.agentknowledge.dto.rag;

import java.util.List;
import java.util.UUID;

public record RunEvaluationCasesBatchResponse(
        UUID experimentId,
        String strategyName,
        int requestedCount,
        int completedCount,
        int failedCount,
        List<Item> items
) {
    public record Item(
            UUID caseId,
            String caseKey,
            UUID runId,
            UUID evaluationId,
            Double groundedScore,
            Double retrievalScore,
            Double recallAtK,
            Double precisionAtK,
            Double mrr,
            Double citationHit,
            String status,
            String errorMessage
    ) {
    }
}
